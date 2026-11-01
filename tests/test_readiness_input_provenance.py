import json
import tempfile
import unittest
from pathlib import Path
from readiness_input_provenance import inspect_inputs, INPUTS

class InputProvenanceTests(unittest.TestCase):
    def test_missing_inputs_are_explicit_blockers(self):
        with tempfile.TemporaryDirectory() as directory:
            result = inspect_inputs(directory)
        self.assertEqual(result["status"], "INPUTS_INCOMPLETE")
        self.assertEqual(set(result["blockers"]), set(INPUTS))
        self.assertFalse(result["orders_allowed"])

    def test_safe_inputs_are_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            for path in INPUTS.values():
                dest = Path(directory) / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps({"status": "RESEARCH_AUDIT", "research_only": True,
                    "orders_allowed": False, "live_trading_approved": False}))
            result = inspect_inputs(directory)
        self.assertEqual(result["status"], "INPUTS_PRESENT")
        self.assertTrue(all(len(item["sha256"]) == 64 for item in result["inputs"].values()))

    def test_unsafe_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / INPUTS["history"]
            dest.parent.mkdir(parents=True)
            dest.write_text(json.dumps({"research_only": True, "orders_allowed": True,
                                        "live_trading_approved": False}))
            result = inspect_inputs(directory)
        self.assertEqual(result["inputs"]["history"]["status"], "UNSAFE_JSON")
        self.assertIn("history", result["blockers"])

    def test_corrupt_json_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / INPUTS["forward_quality"]
            dest.parent.mkdir(parents=True)
            dest.write_text("{invalid")
            result = inspect_inputs(directory)
        self.assertEqual(result["inputs"]["forward_quality"]["status"], "UNREADABLE_OR_INVALID_JSON")

if __name__ == "__main__":
    unittest.main()
