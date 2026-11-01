import unittest
from small_budget_study import small_budget_study


class SmallBudgetTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"AAPL": [100.0 + i * .05 for i in range(75)]}

    def test_three_budgets_and_two_fees(self):
        report = small_budget_study(self.prices)
        self.assertEqual(set(report["budgets"]), {"20.0", "40.0", "100.0"})
        self.assertEqual(set(report["budgets"]["20.0"]), {"0.001", "0.005"})
        self.assertFalse(report["orders_allowed"])

    def test_five_percent_cap(self):
        report = small_budget_study(self.prices)
        for fees in report["budgets"].values():
            for policies in fees.values():
                for result in policies.values():
                    self.assertLessEqual(result["max_observed_total_allocation"], .05)

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            small_budget_study(self.prices, budgets=(20, -40))

    def test_duplicate_budget(self):
        with self.assertRaises(ValueError):
            small_budget_study(self.prices, budgets=(20, 20.0))

    def test_invalid_fee(self):
        with self.assertRaises(ValueError):
            small_budget_study(self.prices, fees=(float("nan"),))


if __name__ == "__main__":
    unittest.main()
