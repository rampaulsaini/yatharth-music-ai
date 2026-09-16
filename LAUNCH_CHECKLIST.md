# Yatharth Music AI — Final Launch Checklist

This checklist separates what is already in the repository from the two things that cannot be completed from code alone: a live GPU runtime and account-owned deployment secrets.

## 1. Free mobile AI test — recommended first launch

### Primary: Kaggle free GPU

1. Open `kaggle/Yatharth_Music_AI_Free_GPU.ipynb` from this repository in Kaggle.
2. In Kaggle Notebook Settings, select a GPU accelerator and enable Internet if required.
3. Run the cells from top to bottom.
4. Wait for `ACE-Step READY: True`.
5. Wait for `Yatharth READY: True` and confirm `demo_mode: false` plus `engine_reachable: true`.
6. Open the printed `YATHARTH PUBLIC LINK` on the phone.
7. Generate a short 10–30 second real AI song first.
8. After success, test 60 seconds and then longer durations as the available GPU session allows.

Kaggle's free GPU availability, quotas, assigned hardware and session limits are controlled by Kaggle and can change. The public Cloudflare link is temporary and ends when the runtime/tunnel stops. This path is for free validation and early testing, not guaranteed 24/7 production hosting.

### Fallback: Google Colab

If Kaggle GPU is unavailable, use the robust Colab notebook:

https://colab.research.google.com/github/rampaulsaini/yatharth-music-ai/blob/main/colab/Yatharth_Music_AI_Free_GPU_v2.ipynb

The Colab v2 notebook also waits for ACE-Step and Yatharth readiness before creating its temporary public link.

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
- Free GPU launch notebooks for Kaggle and Colab.
- GPU benchmark script and documentation.

## 3. Hugging Face public demo

This is optional after the free GPU validation path works.

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

No repository change can manufacture free, permanent GPU capacity or create credentials inside the user's GitHub/Kaggle/Hugging Face accounts. Free GPU platforms can change their limits or availability. The repository is deliberately designed so the free Kaggle route is the primary validation path and Colab remains a fallback before any paid infrastructure is introduced.
