"""Semantic trace records for state-changing runtime operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TraceEvent:
    seq: int
    tick: int
    kind: str
    effect_id: str
    source_entity: str
    target_entity: str
    data: tuple[tuple[str, Any], ...]
    state_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": {key: value for key, value in self.data},
            "effect_id": self.effect_id,
            "kind": self.kind,
            "seq": self.seq,
            "source_entity": self.source_entity,
            "state_hash": self.state_hash,
            "target_entity": self.target_entity,
            "tick": self.tick,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> TraceEvent:
        data = value.get("data", {})
        return cls(
            seq=int(value["seq"]),
            tick=int(value["tick"]),
            kind=str(value["kind"]),
            effect_id=str(value["effect_id"]),
            source_entity=str(value["source_entity"]),
            target_entity=str(value["target_entity"]),
            data=tuple(sorted((str(key), item) for key, item in data.items())),
            state_hash=str(value["state_hash"]),
        )
