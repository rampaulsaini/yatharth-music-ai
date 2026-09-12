---
title: Yatharth Music AI
description: Mobile-first AI music creation adapter for Yatharth Music AI
emoji: 🎵
colorFrom: indigo
colorTo: purple
sdk: gradio
app_file: app.py
python_version: "3.12.12"
startup_duration_timeout: 30m
---

# Yatharth Music AI — Hugging Face adapter

This Space provides a lightweight Gradio interface for the Yatharth Music AI API.

## Architecture

`Hugging Face Gradio Space → Yatharth API → ACE-Step / configured music engine`

The adapter is intentionally thin: the Space UI does **not** contain the production music model or API credentials. Generation is performed by the configured Yatharth API and its configured engine.

## Space configuration

Set these Space secrets/environment variables:

- `YATHARTH_API_BASE_URL` — required URL of the deployed Yatharth API.
- `YATHARTH_API_TOKEN` — optional bearer token if the API is protected.
- `YATHARTH_POLL_SECONDS` — optional polling interval; default `2`.
- `YATHARTH_POLL_TIMEOUT_SECONDS` — optional timeout; default `300`.

## ZeroGPU note

ZeroGPU is useful when a Space itself runs GPU-bound model code through `@spaces.GPU`. This adapter does not do that yet because generation remains in the Yatharth backend. Selecting ZeroGPU for this thin adapter therefore does not move ACE-Step generation onto the Space GPU. A future native ZeroGPU engine can be added as a separate backend without changing the public UI contract.

## Deployment

Create a **Gradio Space** and select **ZeroGPU** only if you want to reserve this Space for a future GPU-backed implementation. The current adapter can run on CPU because it calls the Yatharth API remotely.

The GitHub repository includes an optional GitHub Actions sync workflow. Set the repository variable `HF_SPACE_REPO` to your Hugging Face Space ID (for example, `username/yatharth-music-ai`) and the repository secret `HF_TOKEN` to a Hugging Face token with permission to write to that Space. Never commit either value to source code.

After the Space starts, set `YATHARTH_API_BASE_URL` in the Space settings and test the Generate Music button.

## Current limitation

This Space is a public/demo adapter, not an unlimited free GPU service. Hugging Face ZeroGPU uses shared GPU capacity and daily quotas; those limits apply when GPU-backed functions are actually used.
