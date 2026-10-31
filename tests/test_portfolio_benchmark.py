import unittest
from portfolio_benchmark import compare_portfolio_policies
from run_portfolio_benchmark import run_benchmark_report

class PortfolioBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"AAPL": [100.0 + i for i in range(80)],
                       "SPY": [200.0 + i for i in range(80)]}

    def test_same_shared_cap_and_start(self):
        r = compare_portfolio_policies(self.prices)
        for scenario in r["scenarios"].values():
            for key in ("council_guarded", "equal_weight_capped_hold"):
                result = scenario[key]
                self.assertEqual(result["starting_cash"], 100.0)
                self.assertLessEqual(result["max_observed_total_allocation"], 0.05)
                self.assertFalse(result["orders_allowed"])

    def test_benchmark_is_invested_and_profitable_on_rising_series(self):
        r = compare_portfolio_policies(self.prices)
        hold = r["scenarios"]["0.001"]["equal_weight_capped_hold"]
        self.assertGreater(hold["end_equity"], 100)
        self.assertEqual(hold["max_observed_total_allocation"], 0.05)

    def test_higher_fees_do_not_help_benchmark(self):
        r = compare_portfolio_policies(self.prices)
        self.assertLessEqual(
            r["scenarios"]["0.005"]["equal_weight_capped_hold"]["end_equity"],
            r["scenarios"]["0.001"]["equal_weight_capped_hold"]["end_equity"])

    def test_invalid_fee_fails(self):
        for rates in ((), (-0.1,), (1,), ("cheap",)):
            with self.assertRaises(ValueError):
                compare_portfolio_policies(self.prices, fee_rates=rates)

    def test_misaligned_dates_fail_closed(self):
        def fetch(ticker, period="2y"):
            dates = [f"{i:03}" for i in range(80)]
            if ticker == "SPY":
                dates[4] = "999"
            return {"ticker": ticker, "dates": dates, "closes": [100.] * 80}
        self.assertEqual(run_benchmark_report(fetcher=fetch, tickers=("AAPL","SPY"))["status"], "UNAVAILABLE")

    def test_identical_dates_generate_report(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [f"{i:03}" for i in range(80)],
                    "closes": [100. + i for i in range(80)]}
        result = run_benchmark_report(fetcher=fetch, tickers=("AAPL","SPY"))
        self.assertEqual(result["status"], "EXPLORATORY_ONLY")
        self.assertFalse(result["orders_allowed"])

    def test_empty_watchlist_fails(self):
        self.assertEqual(run_benchmark_report(tickers=())["status"], "UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
