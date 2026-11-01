import unittest
from readiness_artifact_contract import validate_readiness_artifact
from research_readiness import assess_research_readiness
from unittest.mock import patch

def component(status):
    return {"status": status, "issues": [], "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}

class ReadinessArtifactContractTests(unittest.TestCase):
    def test_missing_inputs_report_is_valid_but_not_ready(self):
        report = {"status": "MORE_EVIDENCE_REQUIRED", "issues": ["MISSING_OR_INVALID_INPUTS"],
                  "research_only": True, "orders_allowed": False, "live_trading_approved": False}
        result = validate_readiness_artifact(report)
        self.assertEqual(result["readiness_status"], "MORE_EVIDENCE_REQUIRED")

    def test_rejects_unsafe_report(self):
        report = {"status": "MORE_EVIDENCE_REQUIRED", "issues": ["MISSING_OR_INVALID_INPUTS"],
                  "research_only": True, "orders_allowed": True, "live_trading_approved": False}
        with self.assertRaises(ValueError):
            validate_readiness_artifact(report)

    def test_ready_requires_current_archives(self):
        with patch("research_readiness.assess_history_quality", return_value=component("COVERAGE_OK")), patch(
            "research_readiness.assess_archive_health", return_value=component("COVERAGE_OK")):
            report = assess_research_readiness({}, {}, {})
        with self.assertRaises(ValueError):
            validate_readiness_artifact(report)

    def test_inconsistent_reasons_rejected(self):
        report = {"status": "MORE_EVIDENCE_REQUIRED", "issues": ["MISSING_OR_INVALID_INPUTS", "UNEXPECTED"],
                  "research_only": True, "orders_allowed": False, "live_trading_approved": False,
                  "checks": {"history": component("COVERAGE_OK"), "forward": component("COVERAGE_OK")}}
        with self.assertRaises(ValueError):
            validate_readiness_artifact(report)

if __name__ == "__main__":
    unittest.main()
