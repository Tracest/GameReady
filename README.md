# GameReady

GameReady is an experiment in building an AI-native, self-healing game
runtime. Its central promise is not that an AI will never be wrong. It is that
every automated diagnosis and repair must be reproducible, verifiable, and
reversible.

The first milestone is a deliberately small vertical slice:

1. run a deterministic combat scenario;
2. inject a duplicate-delivery defect;
3. capture a machine-readable evidence bundle;
4. replay the incident byte-for-byte at the semantic level;
5. diagnose the violated invariant;
6. propose a bounded repair;
7. validate the repair against the incident and regression scenarios.

The current implementation is a dependency-free Python reference kernel. It
proves the protocols before a performance runtime is introduced.

## Quick start

PowerShell:

```powershell
python .\scripts\verify.py
```

The demo exits successfully only when:

- the injected defect is detected;
- the evidence reproduces exactly;
- the proposed repair removes the violation;
- every regression scenario passes.

Generated evidence is written under `artifacts/`, which is ignored by Git.

## Project map

```text
docs/                         Project charter, architecture, and decisions
schemas/                      Language-neutral evidence contracts
scripts/                      Repeatable local verification gate
src/gameready/                Deterministic reference kernel and repair loop
tests/                        Contract, replay, and end-to-end tests
```

See [the project charter](docs/PROJECT_CHARTER.md) for the product boundary and
[the architecture](docs/ARCHITECTURE.md) for the closed-loop design.
