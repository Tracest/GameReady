"""Language-neutral domain objects for deterministic scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class EntitySpec:
    entity_id: str
    health: int

    def __post_init__(self) -> None:
        if not self.entity_id:
            raise ValueError("entity_id must not be empty")
        if self.health < 0:
            raise ValueError("health must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {"entity_id": self.entity_id, "health": self.health}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> EntitySpec:
        return cls(entity_id=str(value["entity_id"]), health=int(value["health"]))


@dataclass(frozen=True, slots=True)
class DamageCommand:
    """One delivered copy of a logical damage effect."""

    tick: int
    effect_id: str
    source_entity: str
    target_entity: str
    amount: int
    delivery: str

    def __post_init__(self) -> None:
        if self.tick < 0:
            raise ValueError("tick must be non-negative")
        if not self.effect_id:
            raise ValueError("effect_id must not be empty")
        if self.amount <= 0:
            raise ValueError("damage amount must be positive")
        if not self.source_entity or not self.target_entity:
            raise ValueError("source and target entity IDs must not be empty")
        if not self.delivery:
            raise ValueError("delivery must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "delivery": self.delivery,
            "effect_id": self.effect_id,
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "tick": self.tick,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> DamageCommand:
        return cls(
            tick=int(value["tick"]),
            effect_id=str(value["effect_id"]),
            source_entity=str(value["source_entity"]),
            target_entity=str(value["target_entity"]),
            amount=int(value["amount"]),
            delivery=str(value["delivery"]),
        )


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    seed: int
    entities: tuple[EntitySpec, ...]
    commands: tuple[DamageCommand, ...]
    expected_health: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("scenario name must not be empty")
        entity_ids = [entity.entity_id for entity in self.entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("scenario entity IDs must be unique")
        expected_ids = [entity_id for entity_id, _ in self.expected_health]
        if len(expected_ids) != len(set(expected_ids)):
            raise ValueError("expected health IDs must be unique")
        unknown = sorted(set(expected_ids) - set(entity_ids))
        if unknown:
            raise ValueError(f"expected health references unknown entities: {unknown}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "commands": [command.to_dict() for command in self.commands],
            "entities": [entity.to_dict() for entity in self.entities],
            "expected_health": {
                entity_id: health
                for entity_id, health in sorted(self.expected_health)
            },
            "name": self.name,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Scenario:
        expected = value.get("expected_health", {})
        return cls(
            name=str(value["name"]),
            seed=int(value["seed"]),
            entities=tuple(EntitySpec.from_dict(item) for item in value["entities"]),
            commands=tuple(
                DamageCommand.from_dict(item) for item in value["commands"]
            ),
            expected_health=tuple(
                sorted((str(key), int(health)) for key, health in expected.items())
            ),
        )


@dataclass(frozen=True, slots=True)
class EngineConfig:
    damage_policy: str = "naive"

    VALID_DAMAGE_POLICIES = frozenset({"naive", "idempotent_by_effect_id"})

    def __post_init__(self) -> None:
        if self.damage_policy not in self.VALID_DAMAGE_POLICIES:
            raise ValueError(f"unsupported damage policy: {self.damage_policy}")

    def to_dict(self) -> dict[str, Any]:
        return {"damage_policy": self.damage_policy}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> EngineConfig:
        return cls(damage_policy=str(value["damage_policy"]))
