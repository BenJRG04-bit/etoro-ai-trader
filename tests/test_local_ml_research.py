"""Offline checks for free local ML experiment and safety."""
import unittest
from local_ml_research import evaluate_local_model, run_local_ml_research


class LocalMLTests(unittest.TestCase):
    def prices(self, n=400):
        return [100 + i * 0.08 + ((i % 13) - 6) * 0.17 for i in range(n)]

    def test_deterministic_and_safe(self):
        a = evaluate_local_model(self.prices())
        self.assertEqual(a, evaluate_local_model(self.prices()))
        self.assertFalse(a["orders_allowed"])
        self.assertFalse(a["demo_trading_approved"])
        self.assertFalse(a["live_trading_approved"])
        self.assertGreaterEqual(a["holdout_samples"], 40)

    def test_training_does_not_see_holdout_prices(self):
        a = self.prices()
        b = a[:]
        b[-1] *= 1.02
        first = evaluate_local_model(a)
        second = evaluate_local_model(b)
        self.assertEqual(first["training_samples"], second["training_samples"])
        self.assertEqual(first["holdout_samples"], second["holdout_samples"])
        self.assertNotEqual(first["latest_model_up_probability_uncalibrated"],
                            second["latest_model_up_probability_uncalibrated"])

    def test_bad_prices_fail_closed(self):
        for prices in ([], [1] * 239, self.prices()[:-1] + [float("nan")],
                       self.prices()[:-1] + [-1]):
            with self.assertRaises(ValueError):
                evaluate_local_model(prices)

    def test_missing_market_data_no_orders(self):
        def broken(*args, **kwargs):
            raise OSError("offline")
        report = run_local_ml_research(fetcher=broken, tickers=("AAPL",))
        self.assertEqual(report["assets"]["AAPL"]["status"], "UNAVAILABLE")
        self.assertEqual(report["external_ai_api_calls"], 0)
        self.assertFalse(report["orders_allowed"])


if __name__ == "__main__":
    unittest.main()
