import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
ENGINE_URL = os.getenv("MUSIC_ENGINE_URL", "http://127.0.0.1:8001").rstrip("/")
API_KEY = os.getenv("ACESTEP_API_KEY", "").strip()
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "2"))
POLL_TIMEOUT = int(os.getenv("POLL_TIMEOUT_SECONDS", "300"))

app = FastAPI(title="Yatharth Music AI API", version="1.1.0")

origins = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if origins == "*" else [x.strip() for x in origins.split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    prompt: str = Field(default="", max_length=2000)
    lyrics: str = Field(default="", max_length=8000)
    language: str = "Hindi"
    genre: str = "Cinematic"
    mood: str = "Emotional"
    voice: str = "Male"
    duration: int = Field(default=60, ge=10, le=300)
    format: str = "mp3"

class Task:
    def __init__(self, request: GenerateRequest):
        self.id = str(uuid.uuid4())
        self.request = request
        self.status = "queued"
        self.progress = 0
        self.audio_url: Optional[str] = None
        self.metadata: dict[str, Any] = {}
        self.error: Optional[str] = None
        self.created = time.time()
        self.engine_task_id: Optional[str] = None
        self.engine_file: Optional[str] = None

tasks: dict[str, Task] = {}

LANG_MAP = {"Hindi":"hi", "Punjabi":"pa", "English":"en"}
VOICE_MAP = {"Male":"male", "Female":"female", "Duet":"duet", "Instrumental":"instrumental"}

def headers():
    return {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

def build_prompt(r: GenerateRequest) -> str:
    return f"{r.genre}, {r.mood}, {r.voice} vocal style, {r.language} language, polished original song"

async def engine_post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{ENGINE_URL}{path}", json=payload, headers=headers())
        resp.raise_for_status()
        return resp.json()

def unwrap_data(j):
    return j.get("data", j) if isinstance(j, dict) else j

@app.get("/api/health")
async def health():
    return {"ok": True, "demo_mode": DEMO_MODE, "engine_url_configured": bool(ENGINE_URL)}

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    if not req.prompt and not req.lyrics:
        raise HTTPException(400, "prompt or lyrics is required")
    task = Task(req)
    tasks[task.id] = task

    if DEMO_MODE:
        task.status = "completed"
        task.progress = 100
        # Small public test tone is not generated here; frontend will display
        # the task state. Real audio requires ACE-Step.
        task.metadata = {"demo": True, "message": "Connect ACE-Step to receive real audio."}
        return {"task_id": task.id, "status": task.status, "demo": True}

    asyncio.create_task(run_engine_task(task))
    return {"task_id": task.id, "status": task.status, "demo": False}

async def run_engine_task(task: Task):
    task.status = "processing"
    r = task.request
    payload = {
        "prompt": build_prompt(r),
        "lyrics": r.lyrics,
        "thinking": True,
        "vocal_language": LANG_MAP.get(r.language, "en"),
        "audio_duration": r.duration,
        "audio_format": r.format,
    }
    if r.voice == "Instrumental":
        payload["lyrics"] = ""
        payload["prompt"] += ", instrumental"
    try:
        created = unwrap_data(await engine_post("/release_task", payload))
        engine_id = created.get("task_id") if isinstance(created, dict) else None
        if not engine_id:
            raise RuntimeError(f"ACE-Step did not return task_id: {created}")
        task.engine_task_id = engine_id

        started = time.time()
        while time.time() - started < POLL_TIMEOUT:
            await asyncio.sleep(POLL_SECONDS)
            result = unwrap_data(await engine_post("/query_result", {"task_id_list": [engine_id]}))
            if not result:
                continue
            item = result[0]
            status = item.get("status", 0)
            task.progress = 50 if status == 0 else 100
            if status == 2:
                raise RuntimeError(str(item.get("error") or item.get("result") or "ACE-Step generation failed"))
            if status == 1:
                raw = item.get("result")
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                first = parsed[0] if isinstance(parsed, list) and parsed else parsed
                file_path = first.get("file") if isinstance(first, dict) else None
                if not file_path:
                    raise RuntimeError("ACE-Step returned success without an audio file")
                task.engine_file = file_path
                task.metadata = first.get("metas", {}) if isinstance(first, dict) else {}
                task.status = "completed"
                task.progress = 100
                # If the engine file is an absolute/public URL, return it;
                # otherwise our proxy endpoint hides the engine URL.
                if str(file_path).startswith("http://") or str(file_path).startswith("https://"):
                    task.audio_url = str(file_path)
                else:
                    task.audio_url = f"/api/audio/{task.id}"
                return
        raise TimeoutError("Generation timed out")
    except Exception as exc:
        task.status = "failed"
        task.error = str(exc)

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "audio_url": task.audio_url,
        "metadata": task.metadata,
        "error": task.error,
        "demo": DEMO_MODE,
    }

def demo_wav_bytes(seconds=3, sample_rate=22050):
    import io, math, wave, struct
    seconds = max(1, min(int(seconds), 5))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
        for n in range(sample_rate * seconds):
            t = n / sample_rate
            value = int(7000 * math.sin(2 * math.pi * 220 * t))
            wf.writeframes(struct.pack("<h", value))
    return buf.getvalue()

@app.get("/api/audio/{task_id}")
async def audio(task_id: str):
    task = tasks.get(task_id)
    if not task or task.status != "completed":
        raise HTTPException(404, "audio not ready")
    if DEMO_MODE:
        return Response(content=demo_wav_bytes(), media_type="audio/wav", headers={"Content-Disposition": 'inline; filename="yatharth-demo.wav"'})
    if not task.engine_file:
        raise HTTPException(404, "engine audio path missing")

    path = task.engine_file
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    else:
        # ACE-Step returns /v1/audio?path=...
        url = f"{ENGINE_URL}{path}" if path.startswith("/") else f"{ENGINE_URL}/{path}"

    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=headers()) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(1024 * 256):
                    yield chunk

    return StreamingResponse(stream(), media_type="audio/mpeg", headers={
        "Content-Disposition": 'inline; filename="yatharth-song.mp3"'
    })

@app.get("/api/tasks")
async def list_tasks():
    return [
        {"task_id": t.id, "status": t.status, "created": t.created}
        for t in sorted(tasks.values(), key=lambda x: x.created, reverse=True)[:50]
    ]
