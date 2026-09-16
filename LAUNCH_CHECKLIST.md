# Yatharth Music AI — Final Launch Checklist

This checklist separates what is already in the repository from the two things that cannot be completed from code alone: a live GPU runtime and account-owned deployment secrets.

## 1. Free mobile AI test — recommended first launch

1. Open the robust real-AI Colab notebook:
   https://colab.research.google.com/github/rampaulsaini/yatharth-music-ai/blob/main/colab/Yatharth_Music_AI_Free_GPU_v2.ipynb
2. In Colab, select a GPU runtime when one is available.
3. Run the cells from top to bottom.
4. Wait for the ACE-Step health check to succeed. The v2 notebook waits up to 3 minutes and prints the ACE-Step log if startup fails.
5. Wait for the Yatharth health check to report `demo_mode: false` and `engine_reachable: true`.
6. Open the printed `YATHARTH PUBLIC LINK` on the phone.
7. Generate a short 10–30 second song first.
8. After the first successful generation, increase duration and test MP3/WAV/FLAC as required.

The public link is temporary and ends when the Colab runtime stops.

## 2. What the repository already provides

- FastAPI application and OpenAPI documentation.
- ACE-Step asynchronous task submission and polling.
- Hindi, Punjabi, English, Sanskrit, Urdu and Bengali options.
- Vocal and instrumental modes.
- BPM, key, time-signature, duration and output-format controls.
- Task progress, audio streaming and download.
- PWA/mobile-first interface.
- Demo mode for no-GPU testing.
- Docker deployment files.
- Automated smoke tests through GitHub Actions.
- Optional Hugging Face Gradio adapter and manual sync workflow.

## 3. Hugging Face public demo

This is optional after the Colab path works.

Required account-owned setup:

- Create a Hugging Face Gradio + ZeroGPU Space.
- Create a Hugging Face token with write access to that Space.
- Add the token as GitHub Actions secret `HF_TOKEN`.
- Add GitHub repository variable `HF_SPACE_REPO` with the Space id, for example `username/yatharth-music-ai`.
- Configure `YATHARTH_API_BASE_URL` in the Space settings.
- Configure `YATHARTH_API_TOKEN` only if the API is protected by a token.
- Run `Sync Hugging Face Space` manually from GitHub Actions.

Do not commit tokens or private credentials to the repository.

## 4. Production launch — not required for the free validation stage

Before charging users or promising always-on generation, add:

- Durable task storage (PostgreSQL/Redis).
- Persistent audio/object storage.
- User authentication and account ownership.
- Per-user quotas and abuse controls.
- Billing/subscriptions if monetized.
- Monitoring, logging and backups.
- Dedicated GPU hosting for ACE-Step.
- HTTPS and an exact production `CORS_ORIGINS` allowlist.
- Terms/privacy/provenance review for the actual jurisdiction and model licenses.

## 5. Definition of “working”

The free validation milestone is complete when one real AI song is generated through:

`Phone browser → Yatharth UI → FastAPI → ACE-Step → audio result`

Demo-mode test tones do not count as this milestone.

## 6. Important limitation

No repository change can manufacture free, permanent GPU capacity or create credentials inside the user's GitHub/Hugging Face accounts. Those are external account/infrastructure steps. The repository is deliberately designed so the free Colab route can validate the complete real-AI flow before any paid infrastructure is introduced.
