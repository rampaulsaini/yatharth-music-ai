# Colab startup failure recovery

The Colab free-GPU notebook is a development/testing path, not permanent hosting.

## Known failure fixed in the notebook

ACE-Step imports Lightning → torchmetrics → matplotlib. Colab can preconfigure matplotlib with the notebook-only backend:

`module://matplotlib_inline.backend_inline`

That backend is not a valid headless server backend for this ACE-Step process. The notebook therefore sets:

`MPLBACKEND=Agg`

**before** ACE-Step starts and passes the environment into the subprocess.

## Startup gate

The notebook now:

1. performs environment preflight;
2. starts ACE-Step;
3. waits for `/health`;
4. retries startup a bounded number of times;
5. exposes the Yatharth API only after the engine is healthy;
6. preserves logs for diagnosis.

This removes the dangerous state where the public API is reachable while the real AI engine is dead.

## Production boundary

A Colab runtime and Quick Tunnel can disappear at any time. For 24/7 operation use persistent compute, durable task state, persistent media storage, monitoring, restart/replacement and independent failover.
