"""Evidence-driven diagnosis, repair planning, and sandbox validation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Sequence

from .canonical import canonical_hash
from .engine import DeterministicEngine
from .evidence import EvidenceBundle
from .invariants import evaluate_invariants
from .model import EngineConfig, Scenario
from .replay import ReplayResult, replay_evidence


@dataclass(frozen=True, slots=True)
class Diagnosis:
    status: str
    code: str
    summary: str
    invariant_id: str | None
    evidence_event_seqs: tuple[int, ...]
    confidence_basis: str
    candidate_class: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_class": self.candidate_class,
            "code": self.code,
            "confidence_basis": self.confidence_basis,
            "evidence_event_seqs": list(self.evidence_event_seqs),
            "invariant_id": self.invariant_id,
            "status": self.status,
            "summary": self.summary,
        }


def diagnose_incident(
    bundle: EvidenceBundle,
    replay: ReplayResult | None = None,
) -> Diagnosis:
    replay_result = replay or replay_evidence(bundle)
    if not replay_result.exact:
        return Diagnosis(
            status="blocked",
            code="evidence_not_reproducible",
            summary="The captured incident does not replay exactly.",
            invariant_id=None,
            evidence_event_seqs=(),
            confidence_basis="blocked_by_replay_gate",
            candidate_class=None,
        )

    duplicate = next(
        (
            violation
            for violation in bundle.violations
            if violation.code == "duplicate_effect_application"
            and violation.invariant_id == "effect.exactly_once"
        ),
        None,
    )
    if duplicate is None:
        return Diagnosis(
            status="blocked",
            code="unsupported_violation",
            summary="No supported invariant violation was found.",
            invariant_id=None,
            evidence_event_seqs=(),
            confidence_basis="no_supported_causal_signature",
            candidate_class=None,
        )

    return Diagnosis(
        status="proven",
        code="duplicate_delivery_without_idempotency",
        summary=(
            "Two delivered copies of one logical effect both mutated world state."
        ),
        invariant_id=duplicate.invariant_id,
        evidence_event_seqs=duplicate.related_event_seqs,
        confidence_basis="exact_replay_and_direct_invariant_witness",
        candidate_class="engine_policy.idempotent_effect_application",
    )


@dataclass(frozen=True, slots=True)
class RepairCandidate:
    candidate_id: str
    kind: str
    changes: tuple[tuple[str, str], ...]
    rollback: tuple[tuple[str, str], ...]
    rationale: str
    planner: str

    @classmethod
    def create(
        cls,
        *,
        kind: str,
        changes: tuple[tuple[str, str], ...],
        rollback: tuple[tuple[str, str], ...],
        rationale: str,
        planner: str,
    ) -> RepairCandidate:
        provisional = cls(
            candidate_id="",
            kind=kind,
            changes=changes,
            rollback=rollback,
            rationale=rationale,
            planner=planner,
        )
        payload = provisional.to_dict()
        payload["candidate_id"] = ""
        return replace(
            provisional,
            candidate_id=f"cand-{canonical_hash(payload)[:20]}",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "changes": dict(self.changes),
            "kind": self.kind,
            "planner": self.planner,
            "rationale": self.rationale,
            "rollback": dict(self.rollback),
        }

    def apply(self, base: EngineConfig) -> EngineConfig:
        if self.kind != "engine_policy_change":
            raise ValueError(f"unsupported candidate kind: {self.kind}")
        changes = dict(self.changes)
        unknown = sorted(set(changes) - {"damage_policy"})
        if unknown:
            raise ValueError(f"candidate changes unsupported fields: {unknown}")
        return EngineConfig(
            damage_policy=changes.get("damage_policy", base.damage_policy)
        )


def plan_repair(
    diagnosis: Diagnosis,
    base_config: EngineConfig,
) -> RepairCandidate | None:
    if (
        diagnosis.status != "proven"
        or diagnosis.candidate_class
        != "engine_policy.idempotent_effect_application"
    ):
        return None

    return RepairCandidate.create(
        kind="engine_policy_change",
        changes=(("damage_policy", "idempotent_by_effect_id"),),
        rollback=(("damage_policy", base_config.damage_policy),),
        rationale=(
            "Record successful logical effect IDs and reject duplicate deliveries "
            "before they can mutate state."
        ),
        planner="deterministic_reference_planner.v1",
    )


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "detail": self.detail,
            "name": self.name,
            "passed": self.passed,
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    incident_id: str
    candidate_id: str
    passed: bool
    checks: tuple[ValidationCheck, ...]
    candidate_config: EngineConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_config": self.candidate_config.to_dict(),
            "candidate_id": self.candidate_id,
            "checks": [check.to_dict() for check in self.checks],
            "incident_id": self.incident_id,
            "passed": self.passed,
        }


def validate_candidate(
    bundle: EvidenceBundle,
    diagnosis: Diagnosis,
    candidate: RepairCandidate,
    regressions: Sequence[Scenario],
) -> ValidationReport:
    checks: list[ValidationCheck] = []
    replay = replay_evidence(bundle)
    checks.append(
        ValidationCheck(
            name="original_incident_replays",
            passed=replay.exact,
            detail="exact semantic replay required before candidate evaluation",
        )
    )
    checks.append(
        ValidationCheck(
            name="diagnosis_is_proven",
            passed=diagnosis.status == "proven",
            detail=diagnosis.confidence_basis,
        )
    )

    try:
        candidate_config = candidate.apply(bundle.config)
    except ValueError as exc:
        candidate_config = bundle.config
        checks.append(
            ValidationCheck(
                name="candidate_scope_is_supported",
                passed=False,
                detail=str(exc),
            )
        )
        return _validation_report(bundle, candidate, candidate_config, checks)

    checks.append(
        ValidationCheck(
            name="candidate_scope_is_supported",
            passed=True,
            detail="candidate changes only the declared damage policy",
        )
    )

    incident_run = DeterministicEngine(candidate_config).run(bundle.scenario)
    incident_violations = evaluate_invariants(incident_run.events)
    same_invariant = tuple(
        violation
        for violation in incident_violations
        if violation.invariant_id == diagnosis.invariant_id
    )
    checks.append(
        ValidationCheck(
            name="incident_violation_removed",
            passed=not same_invariant,
            detail=(
                "no matching invariant violations remain"
                if not same_invariant
                else f"{len(same_invariant)} matching violations remain"
            ),
        )
    )
    checks.append(
        _expected_health_check(
            "incident_expected_outcome",
            bundle.scenario,
            incident_run.final_health,
        )
    )

    repeat_run = DeterministicEngine(candidate_config).run(bundle.scenario)
    repeatable = (
        incident_run.final_state_hash == repeat_run.final_state_hash
        and incident_run.trace_digest == repeat_run.trace_digest
    )
    checks.append(
        ValidationCheck(
            name="candidate_is_deterministic",
            passed=repeatable,
            detail="two isolated executions must produce the same state and trace",
        )
    )

    for scenario in regressions:
        run = DeterministicEngine(candidate_config).run(scenario)
        violations = evaluate_invariants(run.events)
        checks.append(
            ValidationCheck(
                name=f"regression.{scenario.name}.invariants",
                passed=not violations,
                detail=(
                    "no invariant violations"
                    if not violations
                    else f"{len(violations)} invariant violations"
                ),
            )
        )
        checks.append(
            _expected_health_check(
                f"regression.{scenario.name}.expected_outcome",
                scenario,
                run.final_health,
            )
        )

    rollback_matches = dict(candidate.rollback) == bundle.config.to_dict()
    checks.append(
        ValidationCheck(
            name="rollback_is_recorded",
            passed=rollback_matches,
            detail=(
                "rollback restores captured incident policy"
                if rollback_matches
                else "rollback does not restore captured incident policy"
            ),
        )
    )

    return _validation_report(bundle, candidate, candidate_config, checks)


def _expected_health_check(
    name: str,
    scenario: Scenario,
    final_health: tuple[tuple[str, int], ...],
) -> ValidationCheck:
    passed = final_health == tuple(sorted(scenario.expected_health))
    return ValidationCheck(
        name=name,
        passed=passed,
        detail=(
            f"expected={dict(scenario.expected_health)}, actual={dict(final_health)}"
        ),
    )


def _validation_report(
    bundle: EvidenceBundle,
    candidate: RepairCandidate,
    candidate_config: EngineConfig,
    checks: list[ValidationCheck],
) -> ValidationReport:
    return ValidationReport(
        incident_id=bundle.incident_id,
        candidate_id=candidate.candidate_id,
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
        candidate_config=candidate_config,
    )
