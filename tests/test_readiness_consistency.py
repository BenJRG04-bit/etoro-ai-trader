import unittest
from copy import deepcopy
from readiness_consistency import validate_readiness_consistency

class ReadinessConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.report = {"status": "RESEARCH_COVERAGE_READY", "issues": [],
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "checks": {name: {"status": "COVERAGE_OK", "research_only": True,
                "orders_allowed": False, "live_trading_approved": False}
                for name in ("history", "forward")}}

    def test_ready_is_consistent(self):
        self.assertEqual(validate_readiness_consistency(self.report)["status"], "CONSISTENT_RESEARCH_ONLY")

    def test_rejects_false_ready(self):
        self.report["checks"]["history"]["status"] = "NEEDS_MORE_EVIDENCE"
        with self.assertRaises(ValueError):
            validate_readiness_consistency(self.report)

    def test_consistent_not_ready(self):
        self.report["checks"]["forward"]["status"] = "NEEDS_MORE_EVIDENCE"
        self.report["status"] = "MORE_EVIDENCE_REQUIRED"
        self.report["issues"] = ["FORWARD_COVERAGE_NOT_READY"]
        self.assertEqual(validate_readiness_consistency(self.report)["status"], "CONSISTENT_RESEARCH_ONLY")

    def test_rejects_false_failure(self):
        self.report["status"] = "MORE_EVIDENCE_REQUIRED"
        self.report["issues"] = ["HISTORY_COVERAGE_NOT_READY"]
        with self.assertRaises(ValueError):
            validate_readiness_consistency(self.report)

    def test_rejects_unsafe_component(self):
        self.report["checks"]["history"]["orders_allowed"] = True
        with self.assertRaises(ValueError):
            validate_readiness_consistency(self.report)

    def test_rejects_duplicate_issues(self):
        self.report["issues"] = ["A", "A"]
        with self.assertRaises(ValueError):
            validate_readiness_consistency(self.report)

    def test_consistent_missing_inputs(self):
        self.report.pop("checks")
        self.report["status"] = "MORE_EVIDENCE_REQUIRED"
        self.report["issues"] = ["MISSING_OR_INVALID_INPUTS"]
        self.assertEqual(validate_readiness_consistency(self.report)["status"], "CONSISTENT_MISSING_INPUTS")

    def test_rejects_missing_checks_without_failure(self):
        self.report.pop("checks")
        with self.assertRaises(ValueError):
            validate_readiness_consistency(self.report)

    def test_rejects_stale_while_ready(self):
        self.report["archive_freshness"] = {"status": "ARCHIVES_STALE_OR_MISSING",
            "issues": ["FORWARD_MISSING_OR_STALE"], "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}
        with self.assertRaises(ValueError):
            validate_readiness_consistency(self.report)

    def test_accepts_stale_and_not_ready(self):
        self.report["archive_freshness"] = {"status": "ARCHIVES_STALE_OR_MISSING",
            "issues": ["FORWARD_MISSING_OR_STALE"], "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}
        self.report["status"] = "MORE_EVIDENCE_REQUIRED"
        self.report["issues"] = ["FORWARD_MISSING_OR_STALE"]
        self.assertEqual(validate_readiness_consistency(self.report)["status"], "CONSISTENT_RESEARCH_ONLY")

if __name__ == "__main__":
    unittest.main()
