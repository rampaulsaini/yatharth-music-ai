---
title: Yatharth Music AI
description: Mobile-first AI music creation adapter for Yatharth Music AI
emoji: 🎵
colorFrom: indigo
colorTo: purple
sdk: gradio
app_file: app.py
python_version: "3.12"
startup_duration_timeout: 30m
---

# Yatharth Music AI — Hugging Face adapter

This Space provides a lightweight Gradio interface for the Yatharth Music AI API.

## Architecture

`Hugging Face Gradio Space → Yatharth API → ACE-Step / configured music engine`

The adapter does not contain production API credentials. Configure these as Space secrets/environment variables:

- `YATHARTH_API_BASE_URL` — required URL of the deployed Yatharth API.
- `YATHARTH_API_TOKEN` — optional bearer token if the API is protected.
- `YATHARTH_POLL_SECONDS` — optional polling interval; default `2`.
- `YATHARTH_POLL_TIMEOUT_SECONDS` — optional timeout; default `300`.

## ZeroGPU note

The repository keeps this adapter deliberately separate from the production engine. Hugging Face ZeroGPU is a shared, quota-limited demo/testing resource rather than unlimited production compute. If a future version runs the music model locally inside the Space, that model path should be isolated behind a `spaces.GPU`-decorated function and tested independently.

## Deployment

Create a **Gradio + ZeroGPU** Space, then upload/copy the contents of this directory so `app.py` is the Space entry point. Set `YATHARTH_API_BASE_URL` in Space settings before testing generation.
