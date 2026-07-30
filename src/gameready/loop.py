"""End-to-end local incident closure pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import write_pretty_json
from .engine import DeterministicEngine
from .evidence import EvidenceBundle
from .invariants import evaluate_invariants
from .model import EngineConfig
from .repair import diagnose_incident, plan_repair, validate_candidate
from .replay import replay_evidence
from .scenarios import duplicate_delivery_incident, repair_regression_scenarios


@dataclass(frozen=True, slots=True)
class ClosureReport:
    incident_id: str
    incident_detected: bool
    exact_replay: bool
    diagnosis_status: str
    candidate_id: str | None
    local_validation_passed: bool
    local_closed: bool
    production_promotion_eligible: bool
    production_status: str
    artifact_paths: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_paths": dict(self.artifact_paths),
            "candidate_id": self.candidate_id,
            "diagnosis_status": self.diagnosis_status,
            "exact_replay": self.exact_replay,
            "incident_detected": self.incident_detected,
            "incident_id": self.incident_id,
            "local_closed": self.local_closed,
            "local_validation_passed": self.local_validation_passed,
            "production_promotion_eligible": self.production_promotion_eligible,
            "production_status": self.production_status,
        }


def run_demo(output_dir: Path) -> ClosureReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario = duplicate_delivery_incident()
    buggy_config = EngineConfig(damage_policy="naive")

    original_run = DeterministicEngine(buggy_config).run(scenario)
    violations = evaluate_invariants(original_run.events)
    evidence = EvidenceBundle.create(original_run, violations)

    paths = {
        "evidence": output_dir / "evidence.json",
        "replay": output_dir / "replay.json",
        "diagnosis": output_dir / "diagnosis.json",
        "candidate": output_dir / "candidate.json",
        "validation": output_dir / "validation.json",
        "closure": output_dir / "closure.json",
    }
    evidence.save(paths["evidence"])

    replay = replay_evidence(evidence)
    write_pretty_json(paths["replay"], replay.to_dict())

    diagnosis = diagnose_incident(evidence, replay)
    write_pretty_json(paths["diagnosis"], diagnosis.to_dict())

    candidate = plan_repair(diagnosis, buggy_config)
    if candidate is None:
        report = ClosureReport(
            incident_id=evidence.incident_id,
            incident_detected=bool(violations),
            exact_replay=replay.exact,
            diagnosis_status=diagnosis.status,
            candidate_id=None,
            local_validation_passed=False,
            local_closed=False,
            production_promotion_eligible=False,
            production_status="not_evaluated",
            artifact_paths=_relative_artifact_paths(output_dir, paths),
        )
        write_pretty_json(paths["closure"], report.to_dict())
        return report

    write_pretty_json(paths["candidate"], candidate.to_dict())
    validation = validate_candidate(
        evidence,
        diagnosis,
        candidate,
        repair_regression_scenarios(),
    )
    write_pretty_json(paths["validation"], validation.to_dict())

    local_closed = (
        bool(violations)
        and replay.exact
        and diagnosis.status == "proven"
        and validation.passed
    )
    report = ClosureReport(
        incident_id=evidence.incident_id,
        incident_detected=bool(violations),
        exact_replay=replay.exact,
        diagnosis_status=diagnosis.status,
        candidate_id=candidate.candidate_id,
        local_validation_passed=validation.passed,
        local_closed=local_closed,
        production_promotion_eligible=False,
        production_status=(
            "not_implemented: deployment, canary monitoring, and live rollback "
            "are outside milestone one"
        ),
        artifact_paths=_relative_artifact_paths(output_dir, paths),
    )
    write_pretty_json(paths["closure"], report.to_dict())
    return report


def _relative_artifact_paths(
    output_dir: Path,
    paths: dict[str, Path],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((name, path.relative_to(output_dir).as_posix()) for name, path in paths.items())
    )
