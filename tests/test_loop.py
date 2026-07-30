from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from gameready.loop import run_demo


class ClosureLoopTests(unittest.TestCase):
    def test_demo_closes_local_incident_and_emits_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            report = run_demo(output)

            self.assertTrue(report.incident_detected)
            self.assertTrue(report.exact_replay)
            self.assertTrue(report.local_validation_passed)
            self.assertTrue(report.local_closed)
            self.assertFalse(report.production_promotion_eligible)

            for relative_path in dict(report.artifact_paths).values():
                self.assertTrue((output / relative_path).is_file())

            closure = json.loads(
                (output / "closure.json").read_text(encoding="utf-8")
            )
            validation = json.loads(
                (output / "validation.json").read_text(encoding="utf-8")
            )

        self.assertTrue(closure["local_closed"])
        self.assertTrue(validation["passed"])
        self.assertGreaterEqual(len(validation["checks"]), 10)


if __name__ == "__main__":
    unittest.main()
