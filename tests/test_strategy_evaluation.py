import unittest
from strategy_evaluation import evaluate_strategies, _assessment
from run_strategy_report import run_strategy_report

class StrategyEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.prices = [100.0 + 0.1 * i for i in range(240)]

    def test_three_policies_two_periods_two_costs(self):
        r = evaluate_strategies(self.prices)
        self.assertEqual(len(r["policies"]), 3)
        self.assertEqual(set(r["segments"]), {"earlier", "later_holdout"})
        for period in r["segments"].values():
            self.assertEqual(set(period["scenarios"]), {"0.001", "0.005"})
            for policies in period["scenarios"].values():
                self.assertEqual(len(policies), 3)
                for item in policies.values():
                    self.assertLessEqual(item["max_drawdown_fraction"], 1)
        self.assertFalse(r["orders_allowed"])

    def test_later_period_warmup_boundary(self):
        r = evaluate_strategies(self.prices)
        split = r["split_price_index"]
        self.assertEqual(r["segments"]["earlier"]["scored_return_periods"], split - 59)
        self.assertEqual(r["segments"]["later_holdout"]["scored_return_periods"], len(self.prices) - split - 1)

    def test_fee_stress_reduces_capped_hold_value(self):
        r = evaluate_strategies(self.prices)
        segment = r["segments"]["later_holdout"]["scenarios"]
        self.assertLess(segment["0.005"]["capped_hold"]["end_equity"], segment["0.001"]["capped_hold"]["end_equity"])

    def test_crash_blocks_directional_policies(self):
        prices = [100.0] * 60 + [60.0] * 20
        for policy in ("council_guarded", "trend_guarded"):
            self.assertNotEqual(_assessment(prices, policy)["decision"], "POSITIVE_RESEARCH")

    def test_rejects_bad_inputs(self):
        for prices in ([100.0] * 199, [100.0] * 239 + [0.0], [100.0] * 239 + [float("nan")]):
            with self.assertRaises(ValueError):
                evaluate_strategies(prices)
        with self.assertRaises(ValueError):
            evaluate_strategies(self.prices, fee_rates=(float("nan"),))
        with self.assertRaises(ValueError):
            evaluate_strategies(self.prices, holdout_fraction=0.9)

    def test_unavailable_data_is_not_fabricated(self):
        def missing(ticker, period="2y"):
            raise ValueError("Unavailable")
        report = run_strategy_report(fetcher=missing, tickers=("SPY",))
        self.assertEqual(report["assets"]["SPY"]["status"], "UNAVAILABLE")
        self.assertFalse(report["orders_allowed"])

    def test_runner_with_synthetic_data(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [str(i) for i in range(240)], "closes": self.prices}
        report = run_strategy_report(fetcher=fetch, tickers=("SPY",))
        self.assertEqual(report["assets"]["SPY"]["status"], "EXPLORATORY_ONLY")
        self.assertEqual(report["assets"]["SPY"]["split_date"], "168")

if __name__ == "__main__":
    unittest.main()
