import unittest
from risk_veto_outcomes import evaluate_risk_vetoes

class RiskVetoOutcomesTests(unittest.TestCase):
    def test_flat_market_counts(self):
        r = evaluate_risk_vetoes([100.0] * 80)
        self.assertEqual(r["veto_days"]["days"] + r["other_days"]["days"], 20)
        self.assertEqual(r["other_days"]["average_next_day_return_fraction"], 0)
        self.assertFalse(r["orders_allowed"])

    def test_crash_reports_both_groups(self):
        r = evaluate_risk_vetoes([100.0] * 60 + [70.0] * 20)
        self.assertEqual(r["veto_days"]["days"] + r["other_days"]["days"], 20)

    def test_invalid_prices(self):
        with self.assertRaises(ValueError):
            evaluate_risk_vetoes([100.0] * 79 + [float("inf")])

    def test_short_history(self):
        with self.assertRaises(ValueError):
            evaluate_risk_vetoes([100.0] * 40)

if __name__ == "__main__":
    unittest.main()
