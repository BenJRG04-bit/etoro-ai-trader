import unittest
from run_forward_evaluation import run_evaluation
from historical_prices import WATCHLIST

class ForwardEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.dates = [f"2025-{1+i//28:02}-{1+i%28:02}" for i in range(70)]
        self.snapshot = {
            "status": "SNAPSHOT_RESEARCH_ONLY",
            "snapshot": {
                "schema_version": 1, "research_only": True,
                "snapshot_date": self.dates[-1],
                "assets": {t: {"close": 100., "original_positive": False,
                               "confirmed_positive": False, "risk_veto": True}
                           for t in WATCHLIST}
            }
        }

    def fetcher(self, ticker, period="2y"):
        return {"ticker": ticker, "dates": self.dates,
                "closes": [100.] * len(self.dates)}

    def test_no_new_close_is_pending(self):
        r = run_evaluation(self.snapshot, self.fetcher)
        self.assertEqual(r["status"], "PENDING")
        self.assertFalse(r["orders_allowed"])

    def test_new_close_is_observed(self):
        def newer(ticker, period="2y"):
            r = self.fetcher(ticker, period)
            return {**r, "dates": r["dates"] + ["2025-04-01"],
                    "closes": r["closes"] + [101.]}
        r = run_evaluation(self.snapshot, newer)
        self.assertEqual(r["status"], "OBSERVED")
        self.assertAlmostEqual(r["evaluation"]["observations"]["AAPL"]["next_close_return"], 0.01)

    def test_bad_snapshot_fails_closed(self):
        self.assertEqual(run_evaluation({}, self.fetcher)["status"], "UNAVAILABLE")

    def test_incomplete_watchlist_fails_closed(self):
        self.snapshot["snapshot"]["assets"].pop("SPY")
        self.assertEqual(run_evaluation(self.snapshot, self.fetcher)["status"], "UNAVAILABLE")

    def test_missing_snapshot_date_fails_closed(self):
        self.snapshot["snapshot"]["snapshot_date"] = "2024-01-01"
        self.assertEqual(run_evaluation(self.snapshot, self.fetcher)["status"], "UNAVAILABLE")

    def test_revised_snapshot_price_fails_closed(self):
        def revised(ticker, period="2y"):
            row = self.fetcher(ticker, period)
            return {**row, "closes": [101.] * len(self.dates)}
        self.assertEqual(run_evaluation(self.snapshot, revised)["status"], "UNAVAILABLE")

    def test_no_broker_credentials_or_orders(self):
        r = run_evaluation(self.snapshot, self.fetcher)
        self.assertFalse(r["live_trading_approved"])
        self.assertFalse(r["orders_allowed"])

if __name__ == "__main__":
    unittest.main()
