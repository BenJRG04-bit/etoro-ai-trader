import unittest
from run_central_research_cycle import run_research_cycle


def fetch(ticker, period="2y"):
    return {"ticker": ticker, "dates": [str(i).zfill(4) for i in range(120)],
            "closes": [100.0] * 120}


class CentralResearchCycleTests(unittest.TestCase):
    def test_complete_read_only_cycle(self):
        r = run_research_cycle(fetcher=fetch, tickers=("AAPL",))
        self.assertEqual(r["status"], "RESEARCH_CYCLE_COMPLETE")
        self.assertFalse(r["orders_allowed"])
        self.assertEqual(r["asset_count"], 1)

    def test_missing_data_fails_closed(self):
        r = run_research_cycle(fetcher=lambda *a, **k: (_ for _ in ()).throw(ValueError()), tickers=("AAPL",))
        self.assertEqual(r["status"], "UNAVAILABLE")
        self.assertIsNone(r["intelligence"])

    def test_misalignment_fails_closed(self):
        def wrong(ticker, period="2y"):
            row = fetch(ticker, period)
            if ticker == "SPY":
                row["dates"][-1] = "9999"
            return row
        r = run_research_cycle(fetcher=wrong, tickers=("AAPL", "SPY"))
        self.assertEqual(r["status"], "UNAVAILABLE")

    def test_unsafe_decision_fails_closed(self):
        r = run_research_cycle(fetcher=fetch, tickers=("AAPL",),
                               decision_fn=lambda _: {"status": "RESEARCH_ONLY", "research_only": True,
                                                      "orders_allowed": True, "live_trading_approved": False})
        self.assertEqual(r["status"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
