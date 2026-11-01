import unittest
from rolling_decision_audit import rolling_decision_audit

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

def wait(_):
    return {"status": "OK", "decision": "WAIT_RESEARCH", "regime_risk_veto": False}

class RollingAuditTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"A": [100 + .1 * i for i in range(180)]}
    def test_deterministic_windows(self):
        result = rolling_decision_audit(self.prices, window=90, stride=30, council_fn=positive)
        self.assertEqual(result["windows_evaluated"], 4)
        self.assertEqual([x["start_index"] for x in result["windows"]], [0, 30, 60, 90])
        self.assertEqual(result["tied_windows"], 4)
    def test_wait_policy_differs(self):
        result = rolling_decision_audit(self.prices, window=90, stride=90, council_fn=wait)
        self.assertNotEqual(result["windows"][0]["council_minus_baseline"], 0)
    def test_readiness_stays_blocked(self):
        result = rolling_decision_audit(self.prices)
        self.assertFalse(result["orders_allowed"])
        self.assertEqual(result["forward_validation"], "NOT_ESTABLISHED")
    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            rolling_decision_audit(self.prices, window=61)
        with self.assertRaises(ValueError):
            rolling_decision_audit(self.prices, stride=0)
        with self.assertRaises(ValueError):
            rolling_decision_audit(self.prices, starting_cash=200)
        with self.assertRaises(ValueError):
            rolling_decision_audit({"A": [1]*180, "B": [1]*179})
