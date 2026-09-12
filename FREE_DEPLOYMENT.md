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

## 3. Hugging Face ZeroGPU — experimental public demo route

Hugging Face ZeroGPU is a useful option for a small public experiment, but current ZeroGPU Spaces have important limits: ZeroGPU Spaces are designed for Gradio, and free accounts have a daily GPU quota. Quotas and provider rules can change.

For Yatharth Music AI, the recommended architecture is:

```text
Browser
  -> Yatharth API / UI
  -> small Gradio/ZeroGPU adapter
  -> ACE-Step
  -> generated audio
```

Do not put private engine credentials in browser JavaScript. Do not assume ZeroGPU can provide production-scale 24/7 generation for free.

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
