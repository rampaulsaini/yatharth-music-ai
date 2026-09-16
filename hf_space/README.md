# Yatharth Music AI — Free Hugging Face Route

This Space is the free-first public adapter for Yatharth Music AI.

## Architecture

```text
Phone browser
  -> Hugging Face Gradio Space
  -> Yatharth API
  -> ACE-Step 1.5
  -> generated audio
```

The adapter intentionally does not contain production credentials or model weights. Configure `YATHARTH_API_BASE_URL` (and optional `YATHARTH_API_TOKEN`) in the Space settings.

## Free-use expectation

Hugging Face ZeroGPU is shared and quota-limited. It is suitable for testing, demos, and early validation; it is not a promise of unlimited 24/7 production GPU compute.

For the zero-budget phase, keep generation durations modest (for example 30–60 seconds) while validating the complete real-AI path. Move to dedicated/cloud GPU infrastructure only after usage justifies it.

## Deployment checklist

1. Create a Gradio Space with ZeroGPU hardware.
2. Sync the `hf_space/` directory from the main repository.
3. Set `YATHARTH_API_BASE_URL` to a reachable Yatharth API.
4. If the API is protected, set `YATHARTH_API_TOKEN` as a Space secret.
5. Confirm the API reports `DEMO_MODE=false` and `engine_reachable=true` before testing real generation.
6. Test a 30-second song first, then 60 seconds.

## Important architecture note

The current adapter calls the Yatharth API; ZeroGPU therefore does not magically provide compute to an API hosted somewhere else. For a genuinely free end-to-end ZeroGPU deployment, the ACE-Step inference engine must eventually run inside the ZeroGPU Space (or another free GPU runtime) rather than on a separate paid/private server.

This separation is intentional so the public UI and compute backend can be changed independently without redesigning the Yatharth API contract.
