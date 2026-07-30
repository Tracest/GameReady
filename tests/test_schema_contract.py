from __future__ import annotations

import json
from pathlib import Path
import unittest

from gameready.engine import DeterministicEngine
from gameready.evidence import EvidenceBundle
from gameready.invariants import evaluate_invariants
from gameready.model import EngineConfig
from gameready.scenarios import duplicate_delivery_incident


class SchemaContractTests(unittest.TestCase):
    def test_evidence_contains_every_schema_required_field(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        schema = json.loads(
            (project_root / "schemas" / "evidence-bundle.schema.json").read_text(
                encoding="utf-8"
            )
        )
        run = DeterministicEngine(EngineConfig(damage_policy="naive")).run(
            duplicate_delivery_incident()
        )
        evidence = EvidenceBundle.create(
            run,
            evaluate_invariants(run.events),
        ).to_dict()

        self.assertEqual(
            schema["properties"]["format_version"]["const"],
            evidence["format_version"],
        )
        self.assertEqual(set(schema["required"]), set(evidence))


if __name__ == "__main__":
    unittest.main()
