import unittest
from datetime import date, timedelta
from historical_research_pipeline import run_historical_research
from historical_prices import WATCHLIST


def mock_history(ticker, period="2y"):
    start = date(2024, 1, 1)
    return {
        "ticker": ticker,
        "price_type": "unadjusted_daily_close",
        "dates": [(start + timedelta(days=i)).isoformat()
                  for i in range(180)],
        "closes": [100.0 + i * 0.1 for i in range(180)],
    }


class HistoricalResearchPipelineTests(unittest.TestCase):
    def test_all_five_assets_research_only(self):
        result = run_historical_research(fetcher=mock_history)
        self.assertEqual(set(result["assets"]), set(WATCHLIST))
        self.assertFalse(result["live_trading_approved"])
        for asset in result["assets"].values():
            self.assertEqual(asset["status"], "EXPLORATORY_ONLY")
            self.assertGreaterEqual(asset["evaluation"]["window_count"], 1)
            self.assertFalse(asset["data_audit"]["valid_for_total_return_comparison"])

    def test_failed_ticker_does_not_appear_successful(self):
        def fetch(ticker, period="2y"):
            if ticker == "NVDA":
                raise OSError("provider unavailable")
            return mock_history(ticker, period)
        result = run_historical_research(fetcher=fetch)
        self.assertEqual(
            result["assets"]["NVDA"]["status"],
            "DATA_OR_EVALUATION_UNAVAILABLE"
        )
        self.assertEqual(result["assets"]["AAPL"]["status"], "EXPLORATORY_ONLY")

    def test_insufficient_history_rejected(self):
        def short(ticker, period="2y"):
            data = mock_history(ticker, period)
            data["dates"] = data["dates"][:100]
            data["closes"] = data["closes"][:100]
            return data
        result = run_historical_research(fetcher=short)
        self.assertTrue(all(
            asset["status"] == "DATA_OR_EVALUATION_UNAVAILABLE"
            for asset in result["assets"].values()
        ))


if __name__ == "__main__":
    unittest.main()
