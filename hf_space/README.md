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

This Space is the free-first public music generator for Yatharth Music AI.
It runs the official **ACE-Step 1.5 XL Turbo Diffusers** pipeline directly on
Hugging Face ZeroGPU, so this route does not require a separate Yatharth API
or paid GPU server.

## Architecture

```text
Phone browser
  -> Hugging Face Gradio Space (ZeroGPU)
  -> ACE-Step 1.5 XL Turbo
  -> generated WAV audio
```

## Current free-first limits

- Generation length: 10–60 seconds.
- Default: 30 seconds.
- Languages exposed in the UI: Hindi, Punjabi, English, Sanskrit, Urdu, Bengali.
- Optional lyrics, genre, mood, vocal style and instrumental mode.
- ZeroGPU is shared and quota-limited; this is for validation, demos and early users,
  not unlimited 24/7 production hosting.

## Deployment

1. Create a **public Gradio Space** named `yatharth-music-ai` under the Hugging Face account.
2. Select **ZeroGPU** hardware.
3. Copy/sync the contents of this `hf_space/` directory into the Space repository.
4. Wait for the Space to finish building and downloading the model.
5. Open the Space from a phone browser.
6. First test: Hindi + Cinematic + Emotional + 30 seconds.

The repository also contains a GitHub Actions sync workflow. It requires a Hugging
Face write token stored in GitHub as `HF_TOKEN` and the Space repository id in the
`HF_SPACE_REPO` Actions variable. The workflow is intentionally manual so a token
is never committed to source control.

## Model

The app uses `ACE-Step/acestep-v15-xl-turbo-diffusers`, the official Diffusers-format
ACE-Step 1.5 XL Turbo checkpoint. Turbo uses 8 inference steps in the official
Diffusers pipeline documentation.

## After validation

Keep this ZeroGPU Space as the zero-budget public/demo route. When usage or revenue
justifies dedicated compute, the main Yatharth API can be connected to a dedicated
GPU backend without changing the public product concept.

## Licensing

The ACE-Step model checkpoint is published under the MIT license. Review the current
model card, Hugging Face terms, and any applicable third-party rights before offering
paid music generation commercially.
