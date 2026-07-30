"""Portable incident evidence bundles."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from . import __version__
from .canonical import canonical_hash, read_json, write_pretty_json
from .engine import RunResult
from .invariants import Violation
from .model import EngineConfig, Scenario
from .trace import TraceEvent


EVIDENCE_FORMAT_VERSION = "gameready.evidence.v1"


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    format_version: str
    incident_id: str
    engine_version: str
    scenario: Scenario
    config: EngineConfig
    initial_state_hash: str
    final_state_hash: str
    final_health: tuple[tuple[str, int], ...]
    trace_digest: str
    events: tuple[TraceEvent, ...]
    violations: tuple[Violation, ...]

    @classmethod
    def create(
        cls,
        run: RunResult,
        violations: tuple[Violation, ...],
    ) -> EvidenceBundle:
        provisional = cls(
            format_version=EVIDENCE_FORMAT_VERSION,
            incident_id="",
            engine_version=__version__,
            scenario=run.scenario,
            config=run.config,
            initial_state_hash=run.initial_state_hash,
            final_state_hash=run.final_state_hash,
            final_health=run.final_health,
            trace_digest=run.trace_digest,
            events=run.events,
            violations=violations,
        )
        return replace(
            provisional,
            incident_id=f"inc-{canonical_hash(provisional.identity_payload())[:20]}",
        )

    def identity_payload(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "engine_version": self.engine_version,
            "final_health": dict(self.final_health),
            "final_state_hash": self.final_state_hash,
            "format_version": self.format_version,
            "initial_state_hash": self.initial_state_hash,
            "scenario": self.scenario.to_dict(),
            "trace_digest": self.trace_digest,
            "violations": [violation.to_dict() for violation in self.violations],
        }

    def expected_incident_id(self) -> str:
        return f"inc-{canonical_hash(self.identity_payload())[:20]}"

    def identity_is_valid(self) -> bool:
        return self.incident_id == self.expected_incident_id()

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.identity_payload(),
            "events": [event.to_dict() for event in self.events],
            "incident_id": self.incident_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> EvidenceBundle:
        return cls(
            format_version=str(value["format_version"]),
            incident_id=str(value["incident_id"]),
            engine_version=str(value["engine_version"]),
            scenario=Scenario.from_dict(value["scenario"]),
            config=EngineConfig.from_dict(value["config"]),
            initial_state_hash=str(value["initial_state_hash"]),
            final_state_hash=str(value["final_state_hash"]),
            final_health=tuple(
                sorted(
                    (str(entity_id), int(health))
                    for entity_id, health in value["final_health"].items()
                )
            ),
            trace_digest=str(value["trace_digest"]),
            events=tuple(TraceEvent.from_dict(item) for item in value["events"]),
            violations=tuple(
                Violation.from_dict(item) for item in value["violations"]
            ),
        )

    def save(self, path: Path) -> None:
        write_pretty_json(path, self.to_dict())

    @classmethod
    def load(cls, path: Path) -> EvidenceBundle:
        return cls.from_dict(read_json(path))
