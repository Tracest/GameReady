"""Deterministic game-runtime reference implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_hash
from .model import DamageCommand, EngineConfig, Scenario
from .trace import TraceEvent


@dataclass(frozen=True, slots=True)
class RunResult:
    scenario: Scenario
    config: EngineConfig
    initial_state_hash: str
    final_state_hash: str
    final_health: tuple[tuple[str, int], ...]
    events: tuple[TraceEvent, ...]

    @property
    def trace_digest(self) -> str:
        return canonical_hash([event.to_dict() for event in self.events])


class DeterministicEngine:
    """Runs ordered commands without time, I/O, or ambient random state."""

    def __init__(self, config: EngineConfig) -> None:
        self._config = config

    def run(self, scenario: Scenario) -> RunResult:
        health = {entity.entity_id: entity.health for entity in scenario.entities}
        initial_state_hash = _state_hash(health)
        processed_effects: set[str] = set()
        events: list[TraceEvent] = []

        indexed_commands = tuple(enumerate(scenario.commands))
        ordered_commands = sorted(
            indexed_commands,
            key=lambda pair: (pair[1].tick, pair[0]),
        )

        for _, command in ordered_commands:
            self._record(
                events,
                command,
                "command.received",
                {"amount": command.amount, "delivery": command.delivery},
                health,
            )

            if command.source_entity not in health:
                self._record(
                    events,
                    command,
                    "effect.rejected",
                    {"reason": "source_missing"},
                    health,
                )
                continue

            if command.target_entity not in health:
                self._record(
                    events,
                    command,
                    "effect.rejected",
                    {"reason": "target_missing"},
                    health,
                )
                continue

            if (
                self._config.damage_policy == "idempotent_by_effect_id"
                and command.effect_id in processed_effects
            ):
                self._record(
                    events,
                    command,
                    "effect.rejected",
                    {"reason": "duplicate_effect"},
                    health,
                )
                continue

            before = health[command.target_entity]
            after = max(0, before - command.amount)
            health[command.target_entity] = after
            processed_effects.add(command.effect_id)
            self._record(
                events,
                command,
                "effect.applied",
                {
                    "amount": command.amount,
                    "delivery": command.delivery,
                    "health_after": after,
                    "health_before": before,
                },
                health,
            )

        final_health = tuple(sorted(health.items()))
        return RunResult(
            scenario=scenario,
            config=self._config,
            initial_state_hash=initial_state_hash,
            final_state_hash=_state_hash(health),
            final_health=final_health,
            events=tuple(events),
        )

    @staticmethod
    def _record(
        events: list[TraceEvent],
        command: DamageCommand,
        kind: str,
        data: dict[str, Any],
        health: dict[str, int],
    ) -> None:
        events.append(
            TraceEvent(
                seq=len(events),
                tick=command.tick,
                kind=kind,
                effect_id=command.effect_id,
                source_entity=command.source_entity,
                target_entity=command.target_entity,
                data=tuple(sorted(data.items())),
                state_hash=_state_hash(health),
            )
        )


def _state_hash(health: dict[str, int]) -> str:
    return canonical_hash(
        {"entities": [{"entity_id": key, "health": health[key]} for key in sorted(health)]}
    )
