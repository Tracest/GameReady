"""Executable runtime contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .trace import TraceEvent


@dataclass(frozen=True, slots=True)
class Violation:
    invariant_id: str
    code: str
    tick: int
    event_seq: int
    related_event_seqs: tuple[int, ...]
    effect_id: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "effect_id": self.effect_id,
            "event_seq": self.event_seq,
            "invariant_id": self.invariant_id,
            "message": self.message,
            "related_event_seqs": list(self.related_event_seqs),
            "tick": self.tick,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Violation:
        return cls(
            invariant_id=str(value["invariant_id"]),
            code=str(value["code"]),
            tick=int(value["tick"]),
            event_seq=int(value["event_seq"]),
            related_event_seqs=tuple(
                int(item) for item in value["related_event_seqs"]
            ),
            effect_id=str(value["effect_id"]),
            message=str(value["message"]),
        )


def evaluate_invariants(events: Sequence[TraceEvent]) -> tuple[Violation, ...]:
    """Evaluate every registered invariant over one semantic trace."""

    violations: list[Violation] = []
    violations.extend(_evaluate_effect_exactly_once(events))
    return tuple(violations)


def _evaluate_effect_exactly_once(
    events: Sequence[TraceEvent],
) -> tuple[Violation, ...]:
    first_application: dict[str, int] = {}
    violations: list[Violation] = []

    for event in events:
        if event.kind != "effect.applied":
            continue

        original_seq = first_application.get(event.effect_id)
        if original_seq is None:
            first_application[event.effect_id] = event.seq
            continue

        violations.append(
            Violation(
                invariant_id="effect.exactly_once",
                code="duplicate_effect_application",
                tick=event.tick,
                event_seq=event.seq,
                related_event_seqs=(original_seq, event.seq),
                effect_id=event.effect_id,
                message=(
                    f"logical effect {event.effect_id!r} mutated state more than once"
                ),
            )
        )

    return tuple(violations)
