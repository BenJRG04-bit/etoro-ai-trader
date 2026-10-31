import unittest
from decision_diagnostics import diagnose_decisions

class DecisionDiagnosticsTests(unittest.TestCase):
    def test_flat_market(self):
        r = diagnose_decisions([100.0] * 80)
        self.assertEqual(r["evaluated_days"], 20)
        self.assertEqual(r["nonpositive_decision_before_up_day"], 0)
        self.assertFalse(r["orders_allowed"])

    def test_rising_prices_have_consistent_counts(self):
        r = diagnose_decisions([100.0 + i for i in range(90)])
        self.assertEqual(sum(r["decision_counts"].values()), 30)
        self.assertEqual(sum(r["regime_counts"].values()), 30)

    def test_bad_price_rejected(self):
        with self.assertRaises(ValueError):
            diagnose_decisions([100.0] * 79 + [float("nan")])

    def test_short_series_rejected(self):
        with self.assertRaises(ValueError):
            diagnose_decisions([100.0] * 30)

if __name__ == "__main__":
    unittest.main()
