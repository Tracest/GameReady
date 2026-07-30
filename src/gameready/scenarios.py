"""Deterministic incident and regression scenario fixtures."""

from __future__ import annotations

from .model import DamageCommand, EntitySpec, Scenario


def duplicate_delivery_incident() -> Scenario:
    return Scenario(
        name="duplicate_delivery_incident",
        seed=104729,
        entities=(
            EntitySpec(entity_id="attacker", health=100),
            EntitySpec(entity_id="defender", health=100),
        ),
        commands=(
            DamageCommand(
                tick=10,
                effect_id="effect-hit-001",
                source_entity="attacker",
                target_entity="defender",
                amount=30,
                delivery="local_combat",
            ),
            DamageCommand(
                tick=11,
                effect_id="effect-hit-001",
                source_entity="attacker",
                target_entity="defender",
                amount=30,
                delivery="network_retry",
            ),
        ),
        expected_health=(("attacker", 100), ("defender", 70)),
    )


def unique_attacks_regression() -> Scenario:
    return Scenario(
        name="unique_attacks_regression",
        seed=104759,
        entities=(
            EntitySpec(entity_id="attacker", health=100),
            EntitySpec(entity_id="defender", health=100),
        ),
        commands=(
            DamageCommand(
                tick=1,
                effect_id="effect-hit-a",
                source_entity="attacker",
                target_entity="defender",
                amount=30,
                delivery="local_combat",
            ),
            DamageCommand(
                tick=2,
                effect_id="effect-hit-b",
                source_entity="attacker",
                target_entity="defender",
                amount=30,
                delivery="local_combat",
            ),
        ),
        expected_health=(("attacker", 100), ("defender", 40)),
    )


def multi_target_regression() -> Scenario:
    return Scenario(
        name="multi_target_regression",
        seed=104761,
        entities=(
            EntitySpec(entity_id="attacker", health=100),
            EntitySpec(entity_id="target-a", health=100),
            EntitySpec(entity_id="target-b", health=100),
        ),
        commands=(
            DamageCommand(
                tick=5,
                effect_id="effect-aoe-001:target-a",
                source_entity="attacker",
                target_entity="target-a",
                amount=20,
                delivery="area_effect",
            ),
            DamageCommand(
                tick=5,
                effect_id="effect-aoe-001:target-b",
                source_entity="attacker",
                target_entity="target-b",
                amount=20,
                delivery="area_effect",
            ),
        ),
        expected_health=(
            ("attacker", 100),
            ("target-a", 80),
            ("target-b", 80),
        ),
    )


def lethal_damage_regression() -> Scenario:
    return Scenario(
        name="lethal_damage_regression",
        seed=104773,
        entities=(
            EntitySpec(entity_id="attacker", health=100),
            EntitySpec(entity_id="defender", health=25),
        ),
        commands=(
            DamageCommand(
                tick=3,
                effect_id="effect-lethal-001",
                source_entity="attacker",
                target_entity="defender",
                amount=40,
                delivery="local_combat",
            ),
        ),
        expected_health=(("attacker", 100), ("defender", 0)),
    )


def repair_regression_scenarios() -> tuple[Scenario, ...]:
    return (
        duplicate_delivery_incident(),
        unique_attacks_regression(),
        multi_target_regression(),
        lethal_damage_regression(),
    )
