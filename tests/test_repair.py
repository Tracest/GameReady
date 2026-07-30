from __future__ import annotations

from dataclasses import replace
import unittest

from gameready.engine import DeterministicEngine
from gameready.evidence import EvidenceBundle
from gameready.invariants import evaluate_invariants
from gameready.model import EngineConfig
from gameready.repair import diagnose_incident, plan_repair, validate_candidate
from gameready.scenarios import (
    duplicate_delivery_incident,
    repair_regression_scenarios,
)


def make_bundle() -> EvidenceBundle:
    config = EngineConfig(damage_policy="naive")
    run = DeterministicEngine(config).run(duplicate_delivery_incident())
    return EvidenceBundle.create(run, evaluate_invariants(run.events))


class RepairTests(unittest.TestCase):
    def test_supported_incident_produces_validated_candidate(self) -> None:
        bundle = make_bundle()
        diagnosis = diagnose_incident(bundle)
        candidate = plan_repair(diagnosis, bundle.config)

        self.assertEqual(diagnosis.status, "proven")
        self.assertIsNotNone(candidate)
        assert candidate is not None

        validation = validate_candidate(
            bundle,
            diagnosis,
            candidate,
            repair_regression_scenarios(),
        )
        self.assertTrue(validation.passed)
        self.assertTrue(all(check.passed for check in validation.checks))

    def test_non_reproducible_evidence_blocks_repair(self) -> None:
        bundle = replace(make_bundle(), trace_digest="0" * 64)
        diagnosis = diagnose_incident(bundle)

        self.assertEqual(diagnosis.status, "blocked")
        self.assertEqual(diagnosis.code, "evidence_not_reproducible")
        self.assertIsNone(plan_repair(diagnosis, bundle.config))


if __name__ == "__main__":
    unittest.main()
