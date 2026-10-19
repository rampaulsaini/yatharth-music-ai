# Self-Upgrading AI/ML Agent Policy

## Continuous loop

observe -> classify -> propose -> test -> review/gate -> signed release -> deploy -> verify -> learn

Agents may continuously prepare diagnostics, patches, regression tests and documentation from observed engineering evidence.

## Safe autonomous actions

- retry transient work
- restart unhealthy workers
- requeue interrupted jobs
- quarantine malformed input
- disable an unhealthy provider
- select an already-approved healthy provider
- generate diagnostics
- prepare patches and tests

## Controlled actions

Dependency upgrades, model/provider changes, schema migrations, production configuration changes and new external integrations require deterministic validation and an explicit release gate.

## Never

- expose secrets to an agent
- bypass branch protection
- turn a failed check into a successful check
- fabricate a live stream, publication, revenue or verification result
- self-deploy arbitrary generated code

Self-healing therefore means controlled recovery. Self-upgrading means governed learning and release, not uncontrolled self-modification.
