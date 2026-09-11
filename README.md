# Yatharth Music AI — Version 1.1

Mobile-first, original AI music web app prototype.

## What this version does

Mobile:
Prompt/Lyrics → Generate → Yatharth backend → ACE-Step server → task polling → audio URL → mobile player.

The browser never needs the ACE-Step secret API key. The backend stores the engine URL/key.

## Important

This package does not include AI model weights and does not provide a permanently hosted GPU server.
For real generation, deploy ACE-Step 1.5 on a reachable machine/GPU and set `MUSIC_ENGINE_URL`.

The frontend has DEMO_MODE so you can test the mobile workflow without a model server.

## Quick start — backend

Python 3.11+ recommended.

    cd backend
    python -m venv .venv
    # activate the venv
    pip install -r requirements.txt
    copy .env.example .env     # Windows
    # or: cp .env.example .env

Edit .env:

    DEMO_MODE=true

Then:

    uvicorn main:app --host 0.0.0.0 --port 8080

Open http://localhost:8080/docs

## Real ACE-Step connection

Set:

    DEMO_MODE=false
    MUSIC_ENGINE_URL=http://YOUR-ACE-STEP-SERVER:8001
    ACESTEP_API_KEY=

Then run the backend again.

The adapter uses ACE-Step's documented:
POST /release_task
POST /query_result
GET /v1/audio?path=...

## Frontend

For easiest mobile testing, open frontend/index.html in a browser, or serve the frontend from a web host.

Set the API base in frontend/app.js:

    const API_BASE = "http://YOUR-BACKEND-HOST:8080";

If the frontend is served by the same backend, leave API_BASE empty.

## API

POST /api/generate

JSON:
{
  "prompt": "uplifting cinematic Punjabi song about hope",
  "lyrics": "",
  "language": "Punjabi",
  "genre": "Cinematic",
  "mood": "Epic",
  "voice": "Duet",
  "duration": 60,
  "format": "mp3"
}

Response:
{
  "task_id": "...",
  "status": "queued",
  "demo": false
}

GET /api/tasks/{task_id}

Returns queued / processing / completed / failed.

GET /api/audio/{task_id}

Proxies the generated audio through the backend when ACE-Step returns a server-local /v1/audio path.

## Safety/product notes

- This is an original product; do not copy Suno branding, UI source, private APIs, or proprietary assets.
- Do not train on scraped copyrighted music.
- Do not imitate a named living artist or clone a third-party voice without authorization.
- Add provenance, consent and licensing metadata before commercial launch.
- Commercial-use permission for an AI output is not the same thing as guaranteed copyright protection.
