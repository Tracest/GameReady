"""Exact semantic replay of captured incidents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_hash
from .engine import DeterministicEngine
from .evidence import EVIDENCE_FORMAT_VERSION, EvidenceBundle
from .invariants import evaluate_invariants


@dataclass(frozen=True, slots=True)
class ReplayResult:
    incident_id: str
    exact: bool
    checks: tuple[tuple[str, bool], ...]
    replay_trace_digest: str
    replay_final_state_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": [
                {"name": name, "passed": passed} for name, passed in self.checks
            ],
            "exact": self.exact,
            "incident_id": self.incident_id,
            "replay_final_state_hash": self.replay_final_state_hash,
            "replay_trace_digest": self.replay_trace_digest,
        }


def replay_evidence(bundle: EvidenceBundle) -> ReplayResult:
    run = DeterministicEngine(bundle.config).run(bundle.scenario)
    replay_violations = evaluate_invariants(run.events)
    replay_events = [event.to_dict() for event in run.events]

    checks = (
        ("format_supported", bundle.format_version == EVIDENCE_FORMAT_VERSION),
        ("incident_identity", bundle.identity_is_valid()),
        ("initial_state", run.initial_state_hash == bundle.initial_state_hash),
        ("final_state", run.final_state_hash == bundle.final_state_hash),
        ("final_health", run.final_health == bundle.final_health),
        ("trace_digest", run.trace_digest == bundle.trace_digest),
        (
            "trace_events",
            canonical_hash(replay_events)
            == canonical_hash([event.to_dict() for event in bundle.events]),
        ),
        (
            "violations",
            tuple(item.to_dict() for item in replay_violations)
            == tuple(item.to_dict() for item in bundle.violations),
        ),
    )
    return ReplayResult(
        incident_id=bundle.incident_id,
        exact=all(passed for _, passed in checks),
        checks=checks,
        replay_trace_digest=run.trace_digest,
        replay_final_state_hash=run.final_state_hash,
    )
