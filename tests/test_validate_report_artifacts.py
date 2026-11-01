import json
import tempfile
import unittest
from pathlib import Path
from validate_report_artifacts import validate_report_artifact

class ArtifactContractTests(unittest.TestCase):
    def check(self, name, report):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / name
            path.write_text(json.dumps(report))
            return validate_report_artifact(path)

    def test_valid_missing_evidence(self):
        self.assertTrue(self.check("research_readiness_report.json",
            {"status": "MORE_EVIDENCE_REQUIRED", "research_only": True,
             "orders_allowed": False, "live_trading_approved": False})["valid"])

    def test_rejects_orders(self):
        with self.assertRaises(ValueError):
            self.check("research_readiness_report.json",
                {"status": "MORE_EVIDENCE_REQUIRED", "research_only": True,
                 "orders_allowed": True, "live_trading_approved": False})

    def test_rejects_wrong_status(self):
        with self.assertRaises(ValueError):
            self.check("council_history_quality.json",
                {"status": "LIVE", "research_only": True,
                 "orders_allowed": False, "live_trading_approved": False})

    def test_rejects_unknown_filename(self):
        with self.assertRaises(ValueError):
            self.check("orders.json", {"status": "RESEARCH", "research_only": True,
                                      "orders_allowed": False, "live_trading_approved": False})

    def test_rejects_non_object(self):
        with self.assertRaises(ValueError):
            self.check("research_readiness_report.json", [])

if __name__ == "__main__":
    unittest.main()
