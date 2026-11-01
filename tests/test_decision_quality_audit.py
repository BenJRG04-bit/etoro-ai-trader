import unittest
from decision_quality_audit import audit_decision_quality

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

def negative(_):
    return {"status": "OK", "decision": "WAIT_RESEARCH", "regime_risk_veto": False}

class DecisionQualityTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"A": [100 + i * .1 for i in range(90)]}
    def test_identical_signals_match_baseline(self):
        report = audit_decision_quality(self.prices, council_fn=positive)
        for cases in report["budgets"].values():
            for row in cases.values():
                self.assertEqual(row["council_minus_capped_hold"], 0)
    def test_waiting_council_differs_from_baseline(self):
        report = audit_decision_quality(self.prices, budgets=(100,), council_fn=negative)
        self.assertNotEqual(report["budgets"]["100"]["fees_only"]["council_minus_capped_hold"], 0)
    def test_three_budgets_three_scenarios(self):
        report = audit_decision_quality(self.prices)
        self.assertEqual(len(report["budgets"]), 3)
        self.assertEqual(len(report["budgets"]["20"]), 3)
        self.assertEqual(report["live_trading_readiness"], "BLOCKED")
    def test_rejects_unsafe_inputs(self):
        with self.assertRaises(ValueError):
            audit_decision_quality(self.prices, budgets=(200,))
        with self.assertRaises(ValueError):
            audit_decision_quality(self.prices, scenarios={"bad": {"unknown": 1}})
