# Yatharth Music AI

Original, mobile-first AI music creation app powered by FastAPI and ACE-Step.

## What is included

- Prompt + lyrics based music creation
- Hindi, Punjabi, English, Sanskrit, Urdu and Bengali UI options
- Cinematic, Pop, Folk, Lo-fi, Hip-Hop, Acoustic, Classical, Ambient and Rock styles
- Male, Female, Duet and Instrumental modes
- BPM, key, time-signature, duration and audio-format controls
- Task queue/polling with progress
- Audio streaming and download
- Local My Songs history
- Random sample idea endpoint
- Responsive mobile-first PWA UI
- FastAPI OpenAPI docs at `/api/docs`
- Health and configuration endpoints
- Basic rate limiting and security headers
- Docker deployment
- GitHub Actions smoke CI

## Final launch checklist

Use [`LAUNCH_CHECKLIST.md`](./LAUNCH_CHECKLIST.md) as the canonical final checklist. It distinguishes the repository work from account-owned deployment steps and gives the exact free mobile validation milestone.

## Free AI testing — Google Colab

The repository includes a ready-to-run free GPU notebook that starts **ACE-Step 1.5 + the Yatharth backend** and creates a temporary HTTPS link for phone/browser testing.

**Open directly in Colab:**

https://colab.research.google.com/github/rampaulsaini/yatharth-music-ai/blob/main/colab/Yatharth_Music_AI_Free_GPU.ipynb

The notebook uses a temporary Cloudflare Tunnel link. No Hugging Face account is required for this development/test route. The link and GPU runtime stop when the Colab runtime stops, so this is not permanent hosting.

## Local development

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/`.

## Demo mode

The default `.env.example` uses `DEMO_MODE=true`. This allows the entire browser/API flow to be tested without a GPU or AI engine. Demo playback is a short test tone and is **not** an AI-generated song.

## Real AI generation

Run a reachable ACE-Step server and configure:

```env
DEMO_MODE=false
MUSIC_ENGINE_URL=http://YOUR-ACE-STEP-SERVER:8001
ACESTEP_API_KEY=
```

The backend uses the ACE-Step task flow (`/release_task` and `/query_result`) and proxies the returned audio. Keep all engine credentials on the server; never place them in frontend JavaScript.

## API

- `POST /api/generate` — create a music task
- `GET /api/tasks/{task_id}` — poll task status
- `GET /api/tasks` — recent tasks
- `GET /api/audio/{task_id}` — stream generated audio
- `DELETE /api/tasks/{task_id}` — delete an owned task
- `POST /api/random-sample` — get a creative starting point
- `POST /api/format-input` — pass input through the engine formatter when supported
- `GET /api/health` — service and engine health
- `GET /api/config` — public UI capability configuration
- `GET /api/docs` — interactive OpenAPI documentation

## Docker

```bash
docker build -t yatharth-music-ai .
docker run --env-file .env -p 8080:8080 yatharth-music-ai
```

Or:

```bash
docker compose up --build
```

## Hugging Face deployment

The Hugging Face Space sync workflow remains in the repository, but it is now **manual-only** so an invalid/missing Hugging Face credential cannot break normal GitHub development. To use it, create a Hugging Face Space and configure the GitHub repository secret `HF_TOKEN` plus the optional `HF_SPACE_REPO` repository variable, then run the workflow manually from GitHub Actions.

## Production requirements

For a public commercial service, the current repository is a strong application baseline but is **not a complete commercial SaaS by itself**. Add PostgreSQL/Redis for durable multi-instance task state, object storage for generated audio, authentication, per-user quotas, billing, abuse prevention, observability, backups and a GPU deployment for ACE-Step.

Set `CORS_ORIGINS` to exact production origins. Keep `ACESTEP_API_KEY` in your deployment secret manager. Put the service behind HTTPS and a reverse proxy/CDN.

## Safety and rights

Yatharth Music AI uses its own branding and should not copy proprietary branding, private APIs or source code from other music products. Do not train on scraped copyrighted music. Do not imitate a named living artist or clone a third-party voice without authorization. Add provenance, consent and licensing metadata before commercial use. AI output copyright and commercial rights depend on applicable law, licenses and the specific model/provider terms.

## Project direction

The repository is designed so the web application, API and AI engine can evolve independently. The next commercial layer should therefore be implemented around the existing API rather than exposing the GPU engine directly to browsers.
