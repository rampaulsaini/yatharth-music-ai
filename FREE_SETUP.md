# Yatharth Music AI — ₹0 setup

This project supports a free-first development path using the open-source ACE-Step engine.

## 1. Easiest path: local computer

A local computer is the most reliable way to stay at ₹0 because there is no cloud GPU rental. ACE-Step can run with GPU acceleration and also supports CPU-only operation, although CPU generation can be much slower.

### Install

Use Python 3.11 or 3.12. Install the official ACE-Step project and its dependencies from the official repository.

Then start the ACE-Step API on port `8001`.

Set Yatharth Music AI to:

```text
DEMO_MODE=false
MUSIC_ENGINE_URL=http://127.0.0.1:8001
```

Start the Yatharth backend on port `8000`, then open the Yatharth web app.

## 2. Free Colab GPU

Open `colab/Yatharth_Music_AI_Free_GPU.ipynb` in Google Colab and run the cells.

The notebook is intended for temporary development/testing. Free Colab GPU access is dynamic, sessions can terminate, and it is not a dependable 24/7 public hosting solution.

## 3. Hardware guidance

- 6GB+ VRAM: a practical starting point for local GPU use.
- 4GB VRAM: ACE-Step has lower-memory modes, but generation may require more aggressive memory management.
- CPU-only: possible, but expect substantially slower generation.

## 4. Important architecture rule

Do not put model weights, API keys, passwords, or private credentials into this GitHub repository.

The public web app can remain in `DEMO_MODE=true` when no engine is connected. When a local or temporary ACE-Step engine is available, set `DEMO_MODE=false` and point `MUSIC_ENGINE_URL` at it.

## 5. Cost target

**Target: ₹0 for software and development.**

A permanently available public AI music-generation server with guaranteed GPU capacity cannot honestly be promised at ₹0. If the project later needs 24/7 public generation, a paid GPU service may become necessary.

## 6. Official project

Use the official ACE-Step repository and documentation for the engine. Avoid unofficial websites claiming to be the official ACE-Step service.
