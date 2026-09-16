# Yatharth Music AI — RTX 4070 / ACE-Step GPU Benchmark

This benchmark measures the **real Yatharth Music AI → FastAPI → ACE-Step** generation path. It is intended to answer:

- How long does a 30s, 60s, or 180s generation actually take?
- How much GPU power and VRAM are used?
- What is the estimated GPU electricity cost per generation?
- How much audio can one GPU theoretically generate per day?
- What data should be used before setting paid-user limits?

> **Important:** This is a measurement tool, not a promise of performance. Run it on the exact GPU, ACE-Step model, quantization/offload settings, inference settings, and server configuration you intend to sell.

## What it measures

The script submits a real request to `POST /api/generate`, then polls `GET /api/tasks/{task_id}` until the task completes. This means demo tones do **not** count.

During the benchmark it also samples `nvidia-smi` every 0.5 seconds when available and records:

- generation time
- end-to-end request time
- average and peak GPU power
- average and peak VRAM usage
- average GPU utilization
- estimated GPU energy in Wh/kWh
- estimated electricity cost

The electricity calculation uses:

```text
GPU energy (Wh) ≈ average GPU power (W) × generation time (seconds) ÷ 3600
Electricity cost = GPU energy (kWh) × electricity rate (₹/kWh)
```

This **does not** include CPU/RAM/SSD/network/monitor/PSU losses, cooling, hosting, payment fees, tax, maintenance, or the purchase price of the PC/GPU.

## Why 30s / 60s / 180s?

Use three durations because generation speed is not always perfectly linear with requested audio duration:

| Test | Purpose |
|---|---|
| 30 seconds | Fast sanity check and low-latency test |
| 60 seconds | Representative short-song benchmark |
| 180 seconds | Representative 3-minute-song benchmark |

Run them **sequentially**. For capacity planning, keep ACE-Step `batch_size=1` so the benchmark represents one user's generation at a time.

## Requirements

On the machine running Yatharth:

- NVIDIA GPU with a working NVIDIA driver
- `nvidia-smi` available for GPU power/VRAM measurements
- Python 3.10+
- Yatharth Music AI running with `DEMO_MODE=false`
- ACE-Step reachable through `MUSIC_ENGINE_URL`
- Real ACE-Step generation working before benchmarking

The benchmark itself uses Python's standard library and does not require `requests` or another extra package.

## Step 1 — Start the real Yatharth + ACE-Step stack

Make sure the health endpoint reports real AI mode:

```bash
curl http://127.0.0.1:8000/api/health
```

You want values equivalent to:

```json
{
  "ok": true,
  "demo_mode": false,
  "engine_reachable": true
}
```

If `demo_mode` is `true`, **stop**. The benchmark would not measure ACE-Step.

## Step 2 — Check the GPU

```bash
nvidia-smi
```

For an RTX 4070, confirm that the expected NVIDIA GPU is shown and that memory is available before starting the benchmark.

For a live view during testing:

```bash
watch -n 1 nvidia-smi
```

On Windows, use:

```powershell
nvidia-smi -l 1
```

## Step 3 — Run the benchmark

From the repository root:

```bash
python scripts/gpu_benchmark.py
```

Default tests:

```text
30s → 60s → 180s
```

The default electricity rate is ₹8/kWh. **Change this to your actual tariff.** For example:

```bash
python scripts/gpu_benchmark.py --electricity-rate 6.50
```

The results are saved to:

```text
gpu_benchmark_results.json
```

## Custom benchmark

Use a different Yatharth URL:

```bash
python scripts/gpu_benchmark.py --base-url http://127.0.0.1:8000
```

Run only a 60-second test:

```bash
python scripts/gpu_benchmark.py --durations 60
```

Run 30s, 60s, 180s and 300s:

```bash
python scripts/gpu_benchmark.py --durations 30,60,180,300 --timeout 900
```

## What a useful result looks like

Example format only — **these are not RTX 4070 performance claims**:

```text
=== 60s ===
status:              completed
generation time:     28.40s
end-to-end time:     32.10s
avg GPU power:       145.0 W
peak GPU power:      171.0 W
peak VRAM:            9300 MB
avg GPU utilization: 92.0%
estimated GPU energy: 1.144 Wh
estimated electricity: ₹0.0092
```

Your real numbers may be substantially different.

## Capacity calculation

The script reports a simple **generation-time-to-audio-time ratio**:

```text
generation ratio = generation seconds ÷ requested audio seconds
```

For example, if a real 180-second song takes 90 seconds:

```text
90 ÷ 180 = 0.50x
```

That means the GPU is producing audio at approximately twice real-time under that exact test configuration.

A theoretical sequential 24-hour figure would then be:

```text
24 ÷ 0.50 = 48 audio-hours/day
```

### Do not sell the theoretical maximum

Real service capacity must reserve time for:

- queueing
- model warm-up
- failed generations/retries
- API requests
- audio downloads
- maintenance
- GPU thermal limits
- server restarts
- multiple simultaneous users
- safety/moderation checks
- storage and cleanup

For an initial paid service, use the measured benchmark as a baseline and apply a conservative operating margin rather than promising the theoretical maximum.

## Paid-user planning

The benchmark gives **audio capacity**, not a guaranteed number of customers. Convert it to customers only after deciding your plan's monthly generation allowance.

For example:

```text
Monthly audio capacity
÷ average audio minutes consumed per paid user
= theoretical user capacity
```

Then apply a safety/availability margin.

Example planning exercise (not a prediction):

If a measured system can produce 1,000 three-minute songs/month under your chosen operating schedule, and a subscription allows 10 songs/month:

```text
1,000 ÷ 10 = 100 users
```

That is a **capacity calculation**, not a recommendation or guarantee. If users actually consume fewer songs, capacity may be higher; if they consume more, it may be lower.

## GPU purchase recovery

If an RTX 4070 costs ₹69,000, do not calculate recovery from electricity alone.

Track:

```text
GPU/PC purchase
+ electricity
+ internet
+ storage
+ payment fees
+ hosting/domain
+ maintenance
+ taxes
+ refunds/credits
```

Then:

```text
net contribution per paid generation
= price collected
  - variable generation cost
  - payment fee
  - other variable costs
```

And:

```text
break-even generations
= total recoverable investment ÷ net contribution per generation
```

The benchmark supplies the generation-time and estimated GPU-energy inputs needed for this calculation.

## Recommended benchmark procedure for the RTX 4070

When the RTX 4070 is installed:

1. Install the NVIDIA driver and verify `nvidia-smi`.
2. Start ACE-Step with the exact model/settings you intend to use in production.
3. Start Yatharth with `DEMO_MODE=false`.
4. Confirm `/api/health` reports `engine_reachable: true`.
5. Keep `batch_size=1` for the single-user benchmark.
6. Run 30s, 60s and 180s tests.
7. Repeat the 60s test **at least 5 times** if you want a more reliable average.
8. Save `gpu_benchmark_results.json` for comparison.
9. Repeat after changing model quantization, offload, inference steps, or other generation settings.
10. Compare **quality + generation time + VRAM + cost**, not speed alone.

## Important interpretation notes

### 1. GPU power is not whole-PC power

`nvidia-smi` measures reported GPU power draw. A complete PC will consume additional power through the CPU, motherboard, RAM, SSD, fans, PSU losses, and other components.

For a business cost model, measure wall power with a suitable power meter if possible.

### 2. One generation is not necessarily one customer

A customer may regenerate a song several times before downloading a result. Include retries/regenerations when calculating usage limits.

### 3. Concurrent users change the result

This benchmark is intentionally sequential. Once the single-generation baseline is known, run a separate controlled concurrency test before increasing `MAX_CONCURRENT_GENERATIONS`.

Do not simply increase concurrency until the GPU crashes.

### 4. Long songs may change memory/time behavior

Always test the longest duration you intend to sell. The 180-second test is included specifically to expose problems that a 30-second test may miss.

### 5. Benchmark after every major model/configuration change

Record:

- GPU model
- VRAM
- ACE-Step model/checkpoint
- quantization/offload settings
- inference steps
- batch size
- audio format
- requested duration
- generation time
- peak VRAM
- average/peak power
- software versions

This makes future hardware comparisons meaningful.

## Output for business planning

After running the benchmark, bring the generated `gpu_benchmark_results.json` into the project discussion. The key numbers needed for the next calculation are:

```text
30s generation time
60s generation time
180s generation time
peak VRAM
average GPU power
peak GPU power
actual electricity tariff
GPU/PC purchase price
planned price per song or subscription
songs included per user
```

Those figures can then be used to calculate a more realistic **₹/song, monthly capacity, break-even point, and operating-cost model** for Yatharth Music AI.
