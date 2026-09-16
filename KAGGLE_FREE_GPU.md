# Yatharth Music AI — Free GPU path

## Recommended free option: Kaggle GPU

For the current $0 validation phase, use the included Kaggle notebook:

`kaggle/Yatharth_Music_AI_Free_GPU.ipynb`

Open it from the repository in Kaggle, select **GPU** under Notebook Settings → Accelerator, enable Internet if Kaggle requests it, and run the cells from top to bottom.

Kaggle provides free GPU notebook access, but availability, quotas, hardware assignment, and session limits are controlled by Kaggle and can change. Therefore this is a **free testing/validation path**, not a promise of permanent hosting or unlimited production capacity.

## Why Kaggle is the primary free path here

- It provides GPU-backed notebooks without buying a GPU.
- It is suitable for running the full ACE-Step + Yatharth stack for validation.
- It is a better fit for repeatable notebook testing than relying on an always-on free public web server.
- The notebook waits for ACE-Step readiness before starting Yatharth, then waits for Yatharth's `engine_reachable=true` health state before creating the public tunnel.

## Exact test flow

1. Open `kaggle/Yatharth_Music_AI_Free_GPU.ipynb`.
2. Select a GPU accelerator.
3. Enable Internet if required.
4. Run every cell from top to bottom.
5. Wait for `ACE-Step READY: True`.
6. Wait for `Yatharth READY: True`.
7. Copy `YATHARTH PUBLIC LINK`.
8. Open the link on the phone.
9. Generate a 10–30 second real AI song.
10. If successful, test 60 seconds.
11. Only after those tests pass should longer generations be attempted.

## Important limitations

A free Kaggle GPU session can stop, become unavailable, or hit account/platform limits. The public Cloudflare URL is temporary and exists only while the notebook runtime and tunnel are alive.

Do not sell a promise of 24/7 availability while using this free notebook path. It is intended to prove that the real AI generation pipeline works and to let you demonstrate the product before paying for dedicated hardware.

## If Kaggle is unavailable

The existing Colab fallback remains available:

`colab/Yatharth_Music_AI_Free_GPU_v2.ipynb`

Use whichever free GPU runtime is actually available to you that day. Neither free platform should be treated as guaranteed production infrastructure.

## Success definition

The project is considered **real-AI validated** only when:

`Phone → Yatharth UI → FastAPI → ACE-Step 1.5 → actual generated audio`

works without `DEMO_MODE` and without the demo test tone.
