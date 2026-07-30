from __future__ import annotations

import unittest

from gameready.engine import DeterministicEngine
from gameready.invariants import evaluate_invariants
from gameready.model import EngineConfig
from gameready.scenarios import duplicate_delivery_incident


class DeterministicEngineTests(unittest.TestCase):
    def test_naive_policy_exposes_duplicate_effect(self) -> None:
        scenario = duplicate_delivery_incident()
        run = DeterministicEngine(EngineConfig(damage_policy="naive")).run(scenario)
        violations = evaluate_invariants(run.events)

        self.assertEqual(dict(run.final_health)["defender"], 40)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].invariant_id, "effect.exactly_once")
        self.assertEqual(violations[0].related_event_seqs, (1, 3))

    def test_idempotent_policy_rejects_duplicate_delivery(self) -> None:
        scenario = duplicate_delivery_incident()
        run = DeterministicEngine(
            EngineConfig(damage_policy="idempotent_by_effect_id")
        ).run(scenario)

        self.assertEqual(dict(run.final_health)["defender"], 70)
        self.assertEqual(evaluate_invariants(run.events), ())
        rejected = [event for event in run.events if event.kind == "effect.rejected"]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(dict(rejected[0].data)["reason"], "duplicate_effect")

    def test_same_scenario_has_stable_state_and_trace(self) -> None:
        scenario = duplicate_delivery_incident()
        engine = DeterministicEngine(EngineConfig(damage_policy="naive"))

        first = engine.run(scenario)
        second = engine.run(scenario)

        self.assertEqual(first.initial_state_hash, second.initial_state_hash)
        self.assertEqual(first.final_state_hash, second.final_state_hash)
        self.assertEqual(first.trace_digest, second.trace_digest)
        self.assertEqual(first.events, second.events)


if __name__ == "__main__":
    unittest.main()
