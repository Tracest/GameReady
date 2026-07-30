from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from gameready.engine import DeterministicEngine
from gameready.evidence import EvidenceBundle
from gameready.invariants import evaluate_invariants
from gameready.model import EngineConfig
from gameready.replay import replay_evidence
from gameready.scenarios import duplicate_delivery_incident


def make_bundle() -> EvidenceBundle:
    run = DeterministicEngine(EngineConfig(damage_policy="naive")).run(
        duplicate_delivery_incident()
    )
    return EvidenceBundle.create(run, evaluate_invariants(run.events))


class EvidenceTests(unittest.TestCase):
    def test_bundle_round_trip_replays_exactly(self) -> None:
        bundle = make_bundle()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "evidence.json"
            bundle.save(path)
            loaded = EvidenceBundle.load(path)

        self.assertEqual(bundle, loaded)
        self.assertTrue(loaded.identity_is_valid())
        self.assertTrue(replay_evidence(loaded).exact)

    def test_tampered_bundle_fails_closed(self) -> None:
        bundle = make_bundle()
        tampered = replace(bundle, final_state_hash="0" * 64)
        replay = replay_evidence(tampered)

        self.assertFalse(tampered.identity_is_valid())
        self.assertFalse(replay.exact)
        failed = {name for name, passed in replay.checks if not passed}
        self.assertIn("incident_identity", failed)
        self.assertIn("final_state", failed)

    def test_incident_identifier_is_deterministic(self) -> None:
        self.assertEqual(make_bundle().incident_id, make_bundle().incident_id)


if __name__ == "__main__":
    unittest.main()
