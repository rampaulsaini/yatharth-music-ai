# Yatharth Music AI

Original, mobile-first AI music creation app powered by a FastAPI backend and ACE-Step.

## Current release

The repository now contains a working browser frontend, backend API, task polling, demo audio, local song history, PWA manifest, environment template, startup script, and GitHub Actions smoke CI.

### User flow

**Prompt / lyrics → Generate → task polling → audio player → download → My Songs**

The browser does not need the ACE-Step secret key. Keep engine credentials on the backend.

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open the repository's `index.html` through a local/static web server, or serve the project behind the same host as the API.

For a simple backend start command:

```bash
bash start.sh
```

## Demo mode

The default `.env.example` uses:

```env
DEMO_MODE=true
```

This lets you test the complete UI and API flow without an AI model server. Demo playback is a short generated test tone, not an AI song.

## Connect ACE-Step

For real generation, deploy a reachable ACE-Step API server and set:

```env
DEMO_MODE=false
MUSIC_ENGINE_URL=http://YOUR-ACE-STEP-SERVER:8001
ACESTEP_API_KEY=
```

The backend integrates with the ACE-Step task flow using `/release_task`, `/query_result`, and the returned audio path. urlACE-Step official repositoryhttps://github.com/ace-step/ACE-Step-1.5

## API

### POST `/api/generate`

Example:

```json
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
```

Optional advanced fields supported by the API include `bpm`, `key`, `time_signature`, and `instrumental`.

### GET `/api/tasks/{task_id}`

Returns `queued`, `processing`, `completed`, or `failed` plus progress, metadata, audio URL, and errors.

### GET `/api/audio/{task_id}`

Streams the generated audio through the backend when ACE-Step returns a server-local audio path.

### GET `/api/health`

Returns backend status and, when not in demo mode, whether the configured engine is reachable.

## Production checklist

- Put the frontend and FastAPI API behind HTTPS.
- Set `CORS_ORIGINS` to the exact production frontend origin instead of `*`.
- Keep `ACESTEP_API_KEY` in server secrets; never commit it.
- Use persistent storage/Redis/PostgreSQL for multi-instance production deployments instead of the current in-memory task store.
- Use object storage for long-lived audio files rather than keeping a GPU server as permanent file storage.
- Add authentication, per-user quotas, abuse/rate limiting, billing and provenance metadata before public commercial launch.
- Run the ACE-Step worker on suitable GPU infrastructure; the GitHub repository itself does not contain model weights or provide a permanent GPU server.

## Product and safety notes

- Yatharth Music AI uses original product branding and should not copy Suno branding, private APIs, source code, or proprietary assets.
- Do not train on scraped copyrighted music.
- Do not imitate a named living artist or clone a third-party voice without authorization.
- Add provenance, consent, and licensing metadata before commercial launch.
- Permission to commercially use an AI output is not automatically the same as guaranteed copyright protection.
