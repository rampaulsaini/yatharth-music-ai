# Free / ₹0 Deployment Paths

This guide keeps the project free-first. It does **not** promise unlimited free GPU time or 24/7 public AI generation.

## 1. Demo mode — always the easiest zero-cost path

Use:

```env
DEMO_MODE=true
```

The web/API flow works without a GPU. The generated demo audio is only a test tone, not an AI-generated song.

## 2. Temporary free GPU for development

The repository includes `colab/Yatharth_Music_AI_Free_GPU.ipynb`. It starts the official ACE-Step API and lets the Yatharth backend connect to it locally inside the temporary notebook runtime.

Free notebook runtimes can disconnect or change availability. Treat this as development/testing, not dependable public hosting.

## 3. Hugging Face ZeroGPU — public demo adapter

The repository now contains `hf_space/`, a standalone Gradio adapter. It keeps the public UI separate from the production API and engine:

```text
Browser
  -> Hugging Face Gradio Space
  -> YATHARTH_API_BASE_URL
  -> Yatharth API
  -> ACE-Step / configured music engine
  -> generated audio
```

The adapter uses `YATHARTH_API_BASE_URL` and an optional `YATHARTH_API_TOKEN`. Credentials are not hard-coded in the repository.

Current Hugging Face ZeroGPU is shared, quota-limited infrastructure. It is suitable for demonstrations/testing, **not unlimited production compute**. The Space itself is also kept intentionally thin so the AI engine can be upgraded independently.

### Automatic deployment

`.github/workflows/sync-huggingface-space.yml` is included for automatic sync after changes to `hf_space/`.

One-time GitHub setup:

1. Create a fine-grained Hugging Face token with write access to the target Space repository.
2. Add it as the GitHub Actions secret `HF_TOKEN`.
3. Add the GitHub Actions repository variable `HF_SPACE_REPO`, for example `your-hf-username/yatharth-music-ai`.
4. In the Hugging Face Space settings, configure `YATHARTH_API_BASE_URL` and, if required, `YATHARTH_API_TOKEN`.
5. Use a **Gradio + ZeroGPU** Space for the free public-demo route.

The workflow syncs only `hf_space/` into the Space, so the main FastAPI application and deployment files remain separate.

## 4. Local NVIDIA GPU

The repository's Docker Compose file contains an optional `gpu` profile for a local NVIDIA setup. This is the most predictable ₹0 software path if suitable hardware is already available.

```bash
docker compose --profile gpu up --build
```

Configure the API to use:

```env
DEMO_MODE=false
MUSIC_ENGINE_URL=http://acestep:8001
```

## 5. Production later

If the project gains users or revenue, upgrade only when necessary: durable task storage, object storage, authentication, quotas, monitoring, backups and a dedicated GPU service can be added without redesigning the public API.

### Cost principle

The target is **₹0 while developing and validating the product**. A guaranteed, always-on public GPU service cannot honestly be promised at ₹0. Any paid upgrade should be optional and funded only when the project has a clear reason to scale.
