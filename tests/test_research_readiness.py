import unittest
from unittest.mock import patch
from research_readiness import assess_research_readiness

HISTORY_OK = {"status": "COVERAGE_OK", "research_only": True, "orders_allowed": False}
FORWARD_OK = {"status": "COVERAGE_OK", "research_only": True, "orders_allowed": False}

class ResearchReadinessTests(unittest.TestCase):
    def assess(self, history=HISTORY_OK, forward=FORWARD_OK):
        with patch("research_readiness.assess_history_quality", return_value=history), \
             patch("research_readiness.assess_archive_health", return_value=forward):
            return assess_research_readiness({}, {}, {})

    def test_both_coverage_ready(self):
        result = self.assess()
        self.assertEqual(result["status"], "RESEARCH_COVERAGE_READY")
        self.assertFalse(result["live_trading_approved"])

    def test_history_not_ready(self):
        result = self.assess(history={**HISTORY_OK, "status": "NEEDS_MORE_EVIDENCE"})
        self.assertIn("HISTORY_COVERAGE_NOT_READY", result["issues"])

    def test_forward_not_ready(self):
        result = self.assess(forward={**FORWARD_OK, "status": "NEEDS_MORE_EVIDENCE"})
        self.assertIn("FORWARD_COVERAGE_NOT_READY", result["issues"])

    def test_both_not_ready(self):
        result = self.assess(history={**HISTORY_OK, "status": "NEEDS_MORE_EVIDENCE"},
                             forward={**FORWARD_OK, "status": "NEEDS_MORE_EVIDENCE"})
        self.assertEqual(len(result["issues"]), 2)

    def test_rejects_unsafe_history(self):
        with self.assertRaises(ValueError):
            self.assess(history={**HISTORY_OK, "orders_allowed": True})

    def test_rejects_unsafe_forward(self):
        with self.assertRaises(ValueError):
            self.assess(forward={**FORWARD_OK, "research_only": False})

    def test_no_trading_permission(self):
        result = self.assess()
        self.assertTrue(result["research_only"])
        self.assertFalse(result["orders_allowed"])

if __name__ == "__main__":
    unittest.main()
