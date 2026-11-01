import unittest
from portfolio_stress_scenarios import shock_prices, stress_audit


class PortfolioStressScenarioTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"AAPL": [100.0 + i for i in range(80)], "SPY": [200.0 + i for i in range(80)]}

    def test_shock_does_not_modify_input(self):
        result = shock_prices(self.prices, -.25)
        self.assertEqual(self.prices["AAPL"][41], 141)
        self.assertAlmostEqual(result["AAPL"][41], 141 * .75)
        self.assertEqual(result["AAPL"][40], 140)

    def test_stress_reports_safe_scenarios(self):
        report = stress_audit(self.prices, fee_rates=(.001,))
        self.assertEqual(set(report["cases"]), {"unchanged", "drop_10pct", "drop_25pct"})
        self.assertFalse(report["orders_allowed"])
        for case in report["cases"].values():
            for policy in case["0.001"].values():
                self.assertLessEqual(policy["max_observed_total_allocation"], .05)

    def test_rejects_invalid_shock(self):
        for fraction in (float("nan"), 0.2, -1):
            with self.assertRaises(ValueError):
                shock_prices(self.prices, fraction)

    def test_rejects_misaligned_prices(self):
        with self.assertRaises(ValueError):
            shock_prices({"AAPL": [100.] * 80, "SPY": [100.] * 79})


if __name__ == "__main__":
    unittest.main()
