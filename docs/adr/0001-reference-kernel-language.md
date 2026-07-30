# ADR 0001: Begin with a Python protocol reference

- Status: accepted
- Date: 2026-07-30

## Context

GameReady needs to prove deterministic evidence, replay, invariant, diagnosis,
candidate, and validation contracts before investing in a production runtime.
The current development environment has Python 3.12 and Node.js, but no Rust
toolchain.

## Decision

Implement milestone one as a dependency-free Python reference kernel. Keep all
serialized contracts language-neutral and avoid Python-specific object
serialization.

## Consequences

- The first vertical slice can run without installing external packages.
- Protocol and failure semantics can be tested before performance work.
- The reference kernel is not the final high-performance game runtime.
- A future Rust implementation must pass the same contract fixtures and replay
  tests before replacing it.
