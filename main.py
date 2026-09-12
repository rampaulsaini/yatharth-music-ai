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
