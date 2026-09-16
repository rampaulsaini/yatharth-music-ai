---
title: Yatharth Music AI
emoji: 🎵
colorFrom: indigo
colorTo: purple
sdk: gradio
python_version: "3.12.12"
app_file: app.py
hardware: zero-gpu
---

# Yatharth Music AI — Free ACE-Step 1.5 ZeroGPU

This Space is now an **end-to-end free-first demo**. The public Gradio UI runs ACE-Step 1.5 directly inside Hugging Face ZeroGPU, so it does not require a separate Yatharth API or paid GPU server for this route.

## Architecture

```text
Phone browser
  -> Hugging Face Gradio Space (ZeroGPU)
  -> ACE-Step 1.5
  -> generated WAV audio
```

## Free-use expectation

Hugging Face ZeroGPU is shared and quota-limited. Free accounts currently receive a limited daily GPU allowance, so this Space intentionally starts with **10–60 second** generations and a 30-second default. It is suitable for testing, demos, and early validation, not unlimited 24/7 production compute.

## What is implemented

- ACE-Step 1.5 turbo model loaded from Hugging Face.
- Direct text-to-music generation with optional lyrics.
- Hindi, Punjabi, English, Sanskrit, Urdu and Bengali language choices.
- Genre, mood, vocal style and instrumental controls.
- ZeroGPU `@spaces.GPU` execution.
- WAV output directly in the browser.
- No Yatharth API secret required for this free-first Space.

## Deployment checklist

1. The Space must use **Gradio + ZeroGPU hardware**.
2. Keep `hf_space/app.py`, `hf_space/requirements.txt` and this README synced into the Space repository.
3. Wait for the Space build to finish; the first model download can take time because ACE-Step 1.5 is a multi-component model.
4. Open the Space from a phone browser.
5. Test a **30-second** generation first.
6. If successful, test 60 seconds while watching the ZeroGPU quota.

## Important limitation

This is the free validation path. ZeroGPU is shared infrastructure with daily quotas and queueing. It cannot honestly be presented as unlimited free production hosting. When the project gets real users/revenue, the same UI can later be connected back to the Yatharth API and a dedicated GPU backend without redesigning the product.

## Model / licensing note

ACE-Step 1.5 is published under the MIT license, and its model card states that generated music is intended for commercial use. Review the current model and Hugging Face terms before launching a paid service.
