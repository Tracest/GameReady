# GameReady project charter

## Mission

GameReady will make game defects observable, reproducible, diagnosable,
repairable, and safely deployable by autonomous agents.

The project treats autonomy as an evidence problem. A repair is eligible for
promotion only when the system can:

1. reproduce the original failure;
2. identify a concrete violated contract;
3. explain the causal events used by the diagnosis;
4. demonstrate that a bounded candidate removes the failure;
5. pass the required regression and performance gates;
6. produce a rollback artifact.

If any proof is missing, the system fails closed and escalates the incident
instead of silently publishing a guess.

## Product boundary

GameReady can automate correctness only where intent is executable. Safety,
lifecycle, gameplay, networking, persistence, performance, and packaging rules
can be represented as contracts.

Taste questions such as whether a mechanic is fun cannot be inferred from
engine state alone. They require an explicit design target, reference
behaviour, experiment, or human decision.

## Non-negotiable principles

- **Determinism before intelligence.** An agent must be able to rerun its
  experiment.
- **Evidence before diagnosis.** Every conclusion points to concrete events
  and violated contracts.
- **Minimal authority.** Agents receive only the capabilities needed for the
  current stage.
- **Isolation before mutation.** Candidates run in disposable sandboxes.
- **Verification before promotion.** A green local check is not production
  acceptance.
- **Rollback is part of the repair.** A change without a tested rollback path
  is incomplete.
- **Unknown means stop.** Missing evidence never counts as a pass.

## First milestone

The first milestone proves the complete protocol on a small deterministic
combat simulation. A duplicated delivery applies one logical damage effect
twice. GameReady must:

- detect the exactly-once invariant violation;
- save a stable evidence bundle;
- reproduce the same semantic trace;
- isolate the first duplicate application;
- propose an idempotency repair;
- reject or accept it through a sandboxed validation matrix;
- emit a machine-readable closure report.

This milestone intentionally uses a deterministic repair planner. A later
model-backed planner will use the same evidence and candidate interfaces; it
will not bypass the gates.

## Definition of done for an autonomous repair

An incident is closed only when all of the following are true:

- reproduction is exact;
- at least one invariant failed before the repair;
- the failure no longer occurs after the repair;
- explicit outcome assertions pass;
- the regression suite passes;
- all artifacts identify the runtime and policy versions;
- the candidate's scope and rollback are recorded;
- post-deployment monitoring reports no recurrence within its acceptance
  window.

The reference kernel currently implements the first six items. Deployment,
rollback execution, and live acceptance are later milestones.
