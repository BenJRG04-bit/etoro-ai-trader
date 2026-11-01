import unittest
from research_evidence_gate import evaluate_research_evidence

SAFE = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}

class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.audit = {"status": "IN_SAMPLE_ONLY_NO_TRADING_APPROVAL", "forward_validation": "NOT_ESTABLISHED", **SAFE}
        self.rolling = {"status": "RETROSPECTIVE_ROLLING_AUDIT_ONLY", "windows_evaluated": 6,
                        "council_win_fraction": .5, "forward_validation": "NOT_ESTABLISHED", **SAFE}
    def test_forward_evidence_block(self):
        result = evaluate_research_evidence(self.audit, self.rolling)
        self.assertIn("NO_INDEPENDENT_FORWARD_VALIDATION", result["blockers"])
        self.assertFalse(result["orders_allowed"])
    def test_insufficient_history_block(self):
        self.rolling["windows_evaluated"] = 1
        self.assertIn("INSUFFICIENT_HISTORICAL_WINDOWS", evaluate_research_evidence(self.audit, self.rolling)["blockers"])
    def test_even_claimed_forward_evidence_cannot_approve(self):
        self.audit["forward_validation"] = "ESTABLISHED"
        self.rolling["forward_validation"] = "ESTABLISHED"
        result = evaluate_research_evidence(self.audit, self.rolling)
        self.assertEqual(result["evidence_gate"], "BLOCKED")
        self.assertIn("MANUAL_BROKER_RISK_REVIEW_REQUIRED", result["blockers"])
    def test_unsafe_source_rejected(self):
        self.audit["orders_allowed"] = True
        with self.assertRaises(ValueError):
            evaluate_research_evidence(self.audit, self.rolling)
    def test_invalid_window_requirement(self):
        with self.assertRaises(ValueError):
            evaluate_research_evidence(self.audit, self.rolling, minimum_windows=1)
