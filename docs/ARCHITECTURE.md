# GameReady architecture

## Closed-loop pipeline

```text
Scenario
  -> deterministic runtime
  -> semantic trace
  -> invariant evaluator
  -> evidence bundle
  -> exact replay
  -> diagnosis
  -> bounded candidate
  -> sandbox validation matrix
  -> closure report
```

No stage may infer success from the absence of an exception. Each stage emits
an explicit result consumed by the next stage.

## Reference-kernel components

### Deterministic runtime

The runtime consumes a fully ordered scenario. It has no wall-clock reads,
ambient randomness, threads, network access, or hidden global state. Every
state-changing command produces a semantic trace event and a canonical state
hash.

### Trace and evidence

A trace records intent, receipt, application, rejection, and state transition
as separate facts. Evidence bundles contain the scenario, engine policy,
trace, state hashes, and violations required to reproduce an incident.

The JSON contract is language-neutral so a future Rust runtime and external
agents can exchange evidence without importing Python implementation details.

### Invariants

Invariants are executable statements of intent. The first invariant is
`effect.exactly_once`: a logical effect identifier may produce at most one
successful state mutation.

Invariant failures identify both the original and conflicting event sequence
numbers. This creates a small causal slice instead of asking an agent to search
an unbounded log.

### Diagnosis and repair planning

Diagnosis consumes invariant violations and trace evidence. It never edits the
runtime directly. It returns a typed diagnosis with evidence references,
confidence, and candidate repair classes.

The milestone-one planner maps a proven duplicate-effect diagnosis to an
idempotent application policy. A model-backed planner can later propose source
patches through the same candidate contract.

### Sandbox validation

A candidate is tested against:

1. the original incident;
2. explicit expected world state;
3. focused regression scenarios;
4. invariant evaluation;
5. deterministic repeatability.

Validation returns a report with individual gate results. Promotion is allowed
only when every required gate explicitly passes.

## Trust boundaries

```text
Observer      read-only runtime and artifact access
Diagnoser     observer access plus hypothesis generation
Repairer      may create candidates in an isolated workspace
Validator     may execute candidates in a sandbox
Promoter      may publish only a signed, fully passing candidate
Monitor       may trigger rollback but may not invent a new patch
```

Capabilities remain separate even if one AI model performs several roles.

## Evolution path

1. Python protocol reference and deterministic vertical slice.
2. Persistent incident store and property-based scenario generation.
3. Source-level patch sandbox with repository-aware provenance.
4. Rust runtime implementing the stable evidence protocol.
5. Multiplayer, async scheduling, persistence, and visual evidence.
6. Build provenance, canary deployment, monitoring, and automatic rollback.
7. Model-backed investigation and optimization under the same gates.
