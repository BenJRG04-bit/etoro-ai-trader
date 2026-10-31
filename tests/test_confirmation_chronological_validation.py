import unittest
from confirmation_chronological_validation import validate_confirmation_chronologically
from run_chronological_confirmation import run_chronological_confirmation

class ChronologicalConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"AAPL": [100. + i / 5 for i in range(200)],
                       "SPY": [200. + i / 8 for i in range(200)]}

    def test_disjoint_return_periods(self):
        r = validate_confirmation_chronologically(self.prices)
        self.assertEqual(r["split_index"], 140)
        self.assertEqual(r["earlier_evaluation_return_intervals"], 81)
        self.assertEqual(r["later_evaluation_return_intervals"], 59)
        self.assertFalse(r["orders_allowed"])

    def test_both_periods_use_same_fee_scenarios(self):
        r = validate_confirmation_chronologically(self.prices)
        self.assertEqual(set(r["earlier"]["scenarios"]), set(r["later"]["scenarios"]))
        for section in ("earlier", "later"):
            for scenario in r[section]["scenarios"].values():
                for policy in ("existing_council", "two_close_confirmation"):
                    self.assertLessEqual(scenario[policy]["max_observed_total_allocation"], 0.05)
                    self.assertEqual(scenario[policy]["starting_cash"], 100.)

    def test_reject_short_history(self):
        with self.assertRaises(ValueError):
            validate_confirmation_chronologically({"AAPL": [100.] * 159})

    def test_reject_misaligned_lengths(self):
        with self.assertRaises(ValueError):
            validate_confirmation_chronologically({"AAPL": [100.] * 200, "SPY": [100.] * 199})

    def test_reject_invalid_split(self):
        with self.assertRaises(ValueError):
            validate_confirmation_chronologically(self.prices, split_fraction=0.95)

    def test_runner_rejects_date_mismatch(self):
        def fetch(ticker, period="2y"):
            dates = [f"{i:03}" for i in range(200)]
            if ticker == "SPY":
                dates[5] = "999"
            return {"ticker": ticker, "dates": dates, "closes": [100.] * 200}
        self.assertEqual(run_chronological_confirmation(fetcher=fetch, tickers=("AAPL", "SPY"))["status"], "UNAVAILABLE")

    def test_runner_success(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [f"{i:03}" for i in range(200)],
                    "closes": [100. + i / 10 for i in range(200)]}
        r = run_chronological_confirmation(fetcher=fetch, tickers=("AAPL", "SPY"))
        self.assertEqual(r["status"], "EXPLORATORY_ONLY")
        self.assertEqual(r["validation"]["split_index"], 140)

if __name__ == "__main__":
    unittest.main()
