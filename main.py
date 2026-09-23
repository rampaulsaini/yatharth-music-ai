import asyncio
import io
import json
import math
import os
import struct
import time
import uuid
import wave
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
ENGINE_URL = os.getenv("MUSIC_ENGINE_URL", "http://127.0.0.1:8001").rstrip("/")
API_KEY = os.getenv("ACESTEP_API_KEY", "").strip()
POLL_SECONDS = max(0.5, float(os.getenv("POLL_SECONDS", "2")))
POLL_TIMEOUT = max(30, int(os.getenv("POLL_TIMEOUT_SECONDS", "300")))
MAX_CONCURRENT = max(1, int(os.getenv("MAX_CONCURRENT_GENERATIONS", "2")))
RATE_LIMIT = max(1, int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")))
MAX_TASKS = max(100, int(os.getenv("MAX_TASKS_IN_MEMORY", "2000")))
MAX_RATE_CLIENTS = max(100, int(os.getenv("MAX_RATE_LIMIT_CLIENTS", "10000")))
MAX_REQUEST_BYTES = max(4096, int(os.getenv("MAX_REQUEST_BYTES", "32768")))
ROOT = Path(__file__).resolve().parent

app = FastAPI(title="Yatharth Music AI API", version="3.0.1", docs_url="/api/docs", redoc_url="/api/redoc")
origins = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in origins.split(",") if x.strip()], allow_credentials=False, allow_methods=["GET", "POST", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

class GenerateRequest(BaseModel):
    prompt: str = Field(default="", max_length=2000)
    lyrics: str = Field(default="", max_length=8000)
    language: str = Field(default="Hindi", max_length=40)
    genre: str = Field(default="Cinematic", max_length=80)
    mood: str = Field(default="Emotional", max_length=80)
    voice: str = Field(default="Male", max_length=40)
    duration: int = Field(default=60, ge=10, le=300)
    format: str = "mp3"
    bpm: Optional[int] = Field(default=None, ge=40, le=220)
    key: Optional[str] = Field(default=None, max_length=20)
    time_signature: Optional[str] = Field(default=None, max_length=10)
    instrumental: bool = False

    @field_validator("format")
    @classmethod
    def valid_format(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"mp3", "wav", "flac"}:
            raise ValueError("format must be mp3, wav, or flac")
        return value

class Task:
    def __init__(self, request: GenerateRequest, client_id: str):
        self.id = str(uuid.uuid4())
        self.request = request
        self.client_id = client_id
        self.status = "queued"
        self.progress = 0
        self.audio_url: Optional[str] = None
        self.metadata: dict[str, Any] = {}
        self.error: Optional[str] = None
        self.created = time.time()
        self.engine_task_id: Optional[str] = None
        self.engine_file: Optional[str] = None

tasks: dict[str, Task] = {}
engine_slots = asyncio.Semaphore(MAX_CONCURRENT)
rate_windows: dict[str, deque[float]] = defaultdict(deque)
LANG_MAP = {"Hindi": "hi", "Punjabi": "pa", "English": "en", "Sanskrit": "sa", "Urdu": "ur", "Bengali": "bn"}
VOICE_MAP = {"Male": "male", "Female": "female", "Duet": "duet", "Instrumental": "instrumental"}


def client_id(request: Request) -> str:
    if os.getenv("TRUST_PROXY", "false").lower() == "true":
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request) -> str:
    cid = client_id(request)
    now = time.time()
    window = rate_windows[cid]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    window.append(now)
    if len(rate_windows) > MAX_RATE_CLIENTS:
        stale = [key for key, values in rate_windows.items() if not values or now - values[-1] > 60]
        for key in stale:
            rate_windows.pop(key, None)
        while len(rate_windows) > MAX_RATE_CLIENTS:
            oldest = min(rate_windows, key=lambda key: rate_windows[key][-1] if rate_windows[key] else 0)
            rate_windows.pop(oldest, None)
    return cid


def headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}


def build_prompt(request: GenerateRequest) -> str:
    parts: list[str] = []
    if request.prompt.strip():
        parts.append(request.prompt.strip())
    parts.extend([request.genre, request.mood, VOICE_MAP.get(request.voice, request.voice.lower()), f"{request.language} language", "polished original song"])
    return ", ".join(parts)


async def engine_post(path: str, payload: dict[str, Any]) -> Any:
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(f"{ENGINE_URL}{path}", json=payload, headers=headers())
        response.raise_for_status()
        return response.json()


def unwrap_data(value: Any) -> Any:
    return value.get("data", value) if isinstance(value, dict) else value


def parse_result(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def prune_tasks() -> None:
    if len(tasks) <= MAX_TASKS:
        return
    old = sorted(tasks.values(), key=lambda x: x.created)
    for task in old[: len(tasks) - MAX_TASKS]:
        tasks.pop(task.id, None)


@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                return Response("Request body too large", status_code=413, media_type="text/plain")
        except ValueError:
            return Response("Invalid Content-Length", status_code=400, media_type="text/plain")
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "microphone=(), camera=(), geolocation=()"
    return response


@app.get("/api/health")
async def health():
    reachable = False
    if not DEMO_MODE:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{ENGINE_URL}/health", headers=headers())
                reachable = response.status_code < 500
        except Exception:
            reachable = False
    return {"ok": True, "version": app.version, "demo_mode": DEMO_MODE, "engine_url_configured": bool(ENGINE_URL), "engine_reachable": reachable, "active_tasks": sum(t.status in {"queued", "processing"} for t in tasks.values()), "max_concurrent": MAX_CONCURRENT}


@app.get("/api/config")
async def config():
    return {"languages": list(LANG_MAP), "formats": ["mp3", "wav", "flac"], "max_duration": 300, "demo_mode": DEMO_MODE}


@app.post("/api/generate")
async def generate(request: GenerateRequest, http_request: Request):
    cid = enforce_rate_limit(http_request)
    if not request.prompt.strip() and not request.lyrics.strip() and not request.instrumental:
        raise HTTPException(400, "prompt or lyrics is required")
    prune_tasks()
    task = Task(request, cid)
    tasks[task.id] = task
    if DEMO_MODE:
        task.status = "completed"
        task.progress = 100
        task.metadata = {"demo": True, "message": "Connect ACE-Step for real AI music."}
        task.audio_url = f"/api/audio/{task.id}"
        return {"task_id": task.id, "status": task.status, "demo": True}
    asyncio.create_task(run_engine_task(task))
    return {"task_id": task.id, "status": task.status, "demo": False}


@app.post("/api/format-input")
async def format_input(payload: dict[str, Any], http_request: Request):
    enforce_rate_limit(http_request)
    if DEMO_MODE:
        text = str(payload.get("prompt") or payload.get("caption") or "").strip()
        return {"ok": True, "text": text}
    try:
        result = unwrap_data(await engine_post("/format_input", payload))
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(502, f"Music engine format-input failed: {exc}") from exc


@app.post("/api/random-sample")
async def random_sample(http_request: Request):
    enforce_rate_limit(http_request)
    if DEMO_MODE:
        return {"ok": True, "data": {"caption": "cinematic uplifting original song, warm piano, strings, modern drums", "lyrics": ""}}
    try:
        result = unwrap_data(await engine_post("/create_random_sample", {}))
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(502, f"Music engine random-sample failed: {exc}") from exc


async def run_engine_task(task: Task):
    async with engine_slots:
        task.status = "processing"
        request = task.request
        payload: dict[str, Any] = {"prompt": build_prompt(request), "lyrics": "" if request.instrumental or request.voice == "Instrumental" else request.lyrics, "thinking": True, "vocal_language": LANG_MAP.get(request.language, "en"), "audio_duration": request.duration, "audio_format": request.format}
        if request.instrumental or request.voice == "Instrumental":
            payload["prompt"] += ", instrumental"
        if request.bpm is not None:
            payload["bpm"] = request.bpm
        if request.key:
            payload["key_scale"] = request.key
        if request.time_signature:
            payload["time_signature"] = request.time_signature
        try:
            created = unwrap_data(await engine_post("/release_task", payload))
            engine_id = created.get("task_id") if isinstance(created, dict) else None
            if not engine_id:
                raise RuntimeError(f"ACE-Step did not return task_id: {created}")
            task.engine_task_id = str(engine_id)
            started = time.time()
            while time.time() - started < POLL_TIMEOUT:
                await asyncio.sleep(POLL_SECONDS)
                result = unwrap_data(await engine_post("/query_result", {"task_id_list": [engine_id]}))
                if not result:
                    continue
                item = result[0] if isinstance(result, list) else result
                status = item.get("status", 0) if isinstance(item, dict) else 0
                task.progress = min(95, max(5, int(((time.time() - started) / POLL_TIMEOUT) * 95)))
                if status == 2:
                    raise RuntimeError(str(item.get("error") or item.get("result") or "ACE-Step generation failed"))
                if status == 1:
                    parsed = parse_result(item.get("result"))
                    first = parsed[0] if isinstance(parsed, list) and parsed else parsed
                    if not isinstance(first, dict):
                        raise RuntimeError("ACE-Step returned an unexpected result")
                    file_path = first.get("file") or first.get("audio_path") or first.get("url")
                    if not file_path:
                        raise RuntimeError("ACE-Step returned success without an audio file")
                    task.engine_file = str(file_path)
                    task.metadata = first.get("metas", {}) or {}
                    task.status = "completed"
                    task.progress = 100
                    task.audio_url = str(file_path) if str(file_path).startswith(("http://", "https://")) else f"/api/audio/{task.id}"
                    return
            raise TimeoutError("Generation timed out")
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str, http_request: Request):
    cid = client_id(http_request)
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task not found")
    if task.client_id != cid:
        raise HTTPException(403, "not allowed")
    return {"task_id": task.id, "status": task.status, "progress": task.progress, "audio_url": task.audio_url, "metadata": task.metadata, "error": task.error, "demo": DEMO_MODE, "created": task.created}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, http_request: Request):
    cid = client_id(http_request)
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task not found")
    if task.client_id != cid:
        raise HTTPException(403, "not allowed")
    tasks.pop(task_id, None)
    return {"ok": True}


def demo_wav_bytes(seconds: int = 3, sample_rate: int = 22050) -> bytes:
    seconds = max(1, min(int(seconds), 5))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        for n in range(sample_rate * seconds):
            t = n / sample_rate
            value = int(7000 * math.sin(2 * math.pi * 220 * t))
            audio.writeframes(struct.pack("<h", value))
    return buffer.getvalue()


@app.get("/api/audio/{task_id}")
async def audio(task_id: str, http_request: Request):
    cid = client_id(http_request)
    task = tasks.get(task_id)
    if not task or task.status != "completed":
        raise HTTPException(404, "audio not ready")
    if task.client_id != cid:
        raise HTTPException(403, "not allowed")
    if DEMO_MODE:
        return Response(content=demo_wav_bytes(), media_type="audio/wav", headers={"Content-Disposition": 'inline; filename="yatharth-demo.wav"'})
    if not task.engine_file:
        raise HTTPException(404, "engine audio path missing")
    path = task.engine_file
    url = path if path.startswith(("http://", "https://")) else f"{ENGINE_URL}{path if path.startswith('/') else '/' + path}"
    media_type = {"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac"}.get(task.request.format, "application/octet-stream")

    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=headers()) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(262144):
                    yield chunk

    return StreamingResponse(stream(), media_type=media_type, headers={"Content-Disposition": f'inline; filename="yatharth-song.{task.request.format}"'})


@app.get("/api/tasks")
async def list_tasks(http_request: Request):
    cid = client_id(http_request)
    return [{"task_id": t.id, "status": t.status, "created": t.created, "audio_url": t.audio_url} for t in sorted(tasks.values(), key=lambda x: x.created, reverse=True) if t.client_id == cid][:50]


@app.get("/robots.txt")
async def robots():
    return Response("User-agent: *\nAllow: /\nDisallow: /api/\n", media_type="text/plain")


@app.get("/")
async def home():
    return FileResponse(ROOT / "index.html")


for asset in ("app.js", "style.css", "manifest.json"):
    app.get(f"/{asset}")(lambda asset=asset: FileResponse(ROOT / asset))


class StudioPlanRequest(BaseModel):
    idea: str = Field(min_length=1, max_length=12000)
    language: str = Field(default="Hindi", max_length=40)
    format: str = Field(default="Animated Short", max_length=80)
    styles: list[str] = Field(default_factory=list, max_length=8)
    lyrics: str = Field(default="", max_length=8000)

class StudioAgentResult(BaseModel):
    id: str
    role: str
    status: str
    outputs: list[str]
    note: str

class StudioPlanResponse(BaseModel):
    plan_id: str
    status: str
    title: str
    brief: str
    language: str
    format: str
    styles: list[str]
    counts: dict[str, int]
    agents: list[StudioAgentResult]
    review_required: bool
    render_available: bool
    music_engine: str

def _studio_title(idea: str) -> str:
    title = idea.split(".", 1)[0].split("।", 1)[0].strip()
    return (title[:64] or "Untitled Production").strip()

def _studio_counts(idea: str, styles: list[str]) -> dict[str, int]:
    scenes = max(4, min(30, math.ceil(len(idea) / 45)))
    characters = 3 if "Kids & Family" in styles else 2
    shots = scenes * 4
    return {"scenes": scenes, "characters": characters, "shots": shots, "music": 1}

@app.post("/api/studio/plan", response_model=StudioPlanResponse)
async def studio_plan(request: StudioPlanRequest, http_request: Request):
    enforce_rate_limit(http_request)
    idea = request.idea.strip()
    styles = [str(s).strip() for s in request.styles if str(s).strip()][:8]
    counts = _studio_counts(idea, styles)
    agents = [
        StudioAgentResult(id="story-architect", role="story", status="PLANNED", outputs=["logline", "script", "dialogue"], note="Structured story planning prepared."),
        StudioAgentResult(id="character-director", role="characters", status="PLANNED", outputs=["character_bible", "asset_prompts"], note="Character continuity contract prepared."),
        StudioAgentResult(id="storyboard-agent", role="storyboard", status="PLANNED", outputs=["scene_list", "shot_list", "camera_plan"], note="Storyboard and camera hand-off prepared."),
        StudioAgentResult(id="music-agent", role="music", status="PLANNED", outputs=["song", "score", "cue_sheet"], note="Music hand-off prepared; actual generation uses the configured music engine."),
        StudioAgentResult(id="animation-planner", role="animation", status="PLANNED", outputs=["animation_plan", "timing_sheet"], note="Animation production plan prepared; no rendering is claimed."),
        StudioAgentResult(id="film-editor", role="editing", status="PLANNED", outputs=["edit_plan", "delivery_manifest"], note="Editorial delivery contract prepared."),
        StudioAgentResult(id="qc-agent", role="quality", status="REVIEW_REQUIRED", outputs=["qc_report"], note="Human review remains required before publication.")
    ]
    return StudioPlanResponse(
        plan_id=str(uuid.uuid4()),
        status="REVIEW_REQUIRED",
        title=_studio_title(idea),
        brief=idea,
        language=request.language,
        format=request.format,
        styles=styles,
        counts=counts,
        agents=agents,
        review_required=True,
        render_available=not DEMO_MODE,
        music_engine="Yatharth Music AI / ACE-Step adapter"
    )


@app.get("/api/studio/status")
async def studio_status():
    return {
        "ok": True,
        "studio": "Yatharth Creative Studio",
        "mode": "free-first-orchestration",
        "agents": ["story-architect", "character-director", "storyboard-agent", "music-agent", "animation-planner", "film-editor", "qc-agent"],
        "pipeline": ["IDEA", "STORY", "CHARACTERS", "STORYBOARD", "MUSIC", "ANIMATION", "EDITING", "QC", "HUMAN_REVIEW"],
        "render_available": not DEMO_MODE,
        "music_engine": "Yatharth Music AI / ACE-Step adapter",
        "publication_requires_human_review": True,
    }


@app.post("/api/studio/manifest")
async def studio_manifest(request: StudioPlanRequest, http_request: Request):
    enforce_rate_limit(http_request)
    idea = request.idea.strip()
    styles = [str(s).strip() for s in request.styles if str(s).strip()][:8]
    counts = _studio_counts(idea, styles)
    plan_id = str(uuid.uuid4())
    return {
        "schema_version": 1,
        "plan_id": plan_id,
        "status": "REVIEW_REQUIRED",
        "project": {"title": _studio_title(idea), "brief": idea, "language": request.language, "format": request.format, "styles": styles},
        "counts": counts,
        "pipeline": [
            {"stage": "story", "agent": "story-architect", "status": "PLANNED"},
            {"stage": "characters", "agent": "character-director", "status": "PLANNED"},
            {"stage": "storyboard", "agent": "storyboard-agent", "status": "PLANNED"},
            {"stage": "music", "agent": "music-agent", "status": "PLANNED"},
            {"stage": "animation", "agent": "animation-planner", "status": "PLANNED"},
            {"stage": "editing", "agent": "film-editor", "status": "PLANNED"},
            {"stage": "qc", "agent": "qc-agent", "status": "REVIEW_REQUIRED"},
        ],
        "artifacts": ["story.json", "character-bible.json", "storyboard.json", "music-cues.json", "animation-plan.json", "edit-plan.json", "qc-report.json"],
        "policy": {"no_secret_exposure": True, "no_fabricated_rendering_claims": True, "human_review_before_publication": True},
    }


# In-memory Creative Studio production runs. Demo mode creates structured
# planning artifacts without claiming that external animation rendering occurred.
STUDIO_RUNS: dict[str, dict] = {}


@app.post("/api/studio/run")
async def studio_run(request: StudioPlanRequest, http_request: Request):
    enforce_rate_limit(http_request)
    run_id = str(uuid.uuid4())
    idea = request.idea.strip()
    title = _studio_title(idea)
    stages = [
        ("story", "story-architect"),
        ("characters", "character-director"),
        ("storyboard", "storyboard-agent"),
        ("music", "music-agent"),
        ("animation", "animation-planner"),
        ("editing", "film-editor"),
        ("qc", "qc-agent"),
    ]
    run = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "REVIEW_REQUIRED",
        "project": {"title": title, "brief": idea, "language": request.language, "format": request.format, "styles": [str(s).strip() for s in request.styles if str(s).strip()][:8]},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "render_available": not DEMO_MODE,
        "review_required": True,
        "stages": [
            {"stage": stage, "agent": agent, "status": "PLANNED" if stage != "qc" else "REVIEW_REQUIRED",
             "artifact": f"{stage}.json"}
            for stage, agent in stages
        ],
        "artifacts": [
            {"name": "production-manifest.json", "type": "manifest", "status": "READY"},
            *[
                {"name": f"{stage}.json", "type": "planning_artifact",
                 "status": "REVIEW_REQUIRED" if stage == "qc" else "PLANNED"}
                for stage, _ in stages
            ],
        ],
        "policy": {
            "no_secret_exposure": True,
            "no_fabricated_rendering_claims": True,
            "human_review_before_publication": True,
            "provider_neutral_adapters": True,
        },
    }
    STUDIO_RUNS[run_id] = run
    return run


@app.get("/api/studio/runs/{run_id}")
async def studio_run_status(run_id: str):
    run = STUDIO_RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    return run


@app.get("/api/studio/runs/{run_id}/manifest")
async def studio_run_manifest(run_id: str):
    run = STUDIO_RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    return run


@app.post("/api/studio/runs/{run_id}/stages/{stage}/execute")
async def studio_execute_stage(run_id: str, stage: str):
    """Execute one supported orchestration stage without fabricating external media."""
    run = STUDIO_RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    stage = stage.strip().lower()
    stage_map = {item["stage"]: item for item in run["stages"]}
    if stage not in stage_map:
        raise HTTPException(status_code=404, detail="Stage not found")
    item = stage_map[stage]
    ordered = [s["stage"] for s in run["stages"]]
    index = ordered.index(stage)
    if index > 0:
        previous = stage_map[ordered[index - 1]]
        if previous["status"] not in {"COMPLETED", "DONE"}:
            raise HTTPException(status_code=409, detail=f"Previous stage '{ordered[index - 1]}' must be completed first")
    if stage == "music" and not DEMO_MODE:
        item["status"] = "READY"
        item["note"] = "Music stage is ready for the configured ACE-Step adapter; use /api/generate for an actual audio task."
    elif stage in {"animation", "editing"}:
        item["status"] = "READY"
        item["note"] = "Structured hand-off prepared. External rendering/assembly adapter is required."
    elif stage == "qc":
        item["status"] = "REVIEW_REQUIRED"
        run["status"] = "REVIEW_REQUIRED"
        item["note"] = "Human review is required before publication."
    else:
        item["status"] = "COMPLETED"
        item["note"] = "Deterministic structured planning artifact generated; no external media generation claimed."
    item["executed_at"] = datetime.now(timezone.utc).isoformat()
    if stage != "qc" and all(s["status"] in {"COMPLETED", "READY", "DONE"} for s in run["stages"][:-1]):
        run["status"] = "REVIEW_REQUIRED"
    return run


@app.get("/api/studio/runs/{run_id}/artifacts/{artifact_name}")
async def studio_run_artifact(run_id: str, artifact_name: str):
    """Return a deterministic structured planning artifact for a production run."""
    run = STUDIO_RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    safe_name = artifact_name.strip()
    allowed = {item["name"] for item in run["artifacts"]}
    if safe_name not in allowed:
        raise HTTPException(status_code=404, detail="Artifact not found")
    project = run["project"]
    counts = _studio_counts(project["brief"], project.get("styles", []))
    stage_by_name = {stage["stage"]: stage for stage in run["stages"]}
    if safe_name == "production-manifest.json":
        return run
    stage = safe_name.removesuffix(".json")
    stage_meta = stage_by_name.get(stage)
    if not stage_meta:
        raise HTTPException(status_code=404, detail="Artifact stage not found")
    payloads = {
        "story": {"deliverable": "story", "title": project["title"], "brief": project["brief"], "language": project["language"], "format": project["format"], "status": stage_meta["status"]},
        "characters": {"deliverable": "character_bible", "planned_characters": counts["characters"], "continuity": "required", "status": stage_meta["status"]},
        "storyboard": {"deliverable": "storyboard", "planned_scenes": counts["scenes"], "planned_shots": counts["shots"], "status": stage_meta["status"]},
        "music": {"deliverable": "music_cues", "tracks": counts["music"], "adapter": "Yatharth Music AI / ACE-Step", "status": stage_meta["status"]},
        "animation": {"deliverable": "animation_plan", "planned_scenes": counts["scenes"], "render_available": run["render_available"], "status": stage_meta["status"]},
        "editing": {"deliverable": "edit_plan", "assembly": "planned", "publication_gate": "human_review", "status": stage_meta["status"]},
        "qc": {"deliverable": "qc_report", "review_required": run["review_required"], "status": stage_meta["status"]},
    }
    return {"schema_version": 1, "run_id": run_id, "artifact": safe_name, "project": project, "data": payloads[stage], "policy": run["policy"]}
