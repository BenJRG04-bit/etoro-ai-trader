"""End-to-end offline integration tests with deterministic historical-style data."""
import unittest
from datetime import date, timedelta

from historical_research_pipeline import run_historical_research
from historical_research_report import summarize_research
from historical_prices import WATCHLIST


def fixture(ticker, period="2y"):
    start = date(2023, 1, 1)
    closes = [100 + i * 0.08 + (i % 11) * 0.03 for i in range(240)]
    return {
        "ticker": ticker,
        "price_type": "unadjusted_daily_close",
        "dates": [(start + timedelta(days=i)).isoformat() for i in range(240)],
        "closes": closes,
    }


class HistoricalPipelineIntegrationTests(unittest.TestCase):
    def test_complete_pipeline_on_five_assets(self):
        report = summarize_research(run_historical_research(fetcher=fixture))
        self.assertEqual(set(report["assets"]), set(WATCHLIST))
        self.assertFalse(report["live_trading_approved"])
        self.assertTrue(report["research_only"])
        for ticker in WATCHLIST:
            row = report["assets"][ticker]
            self.assertEqual(row["status"], "EXPLORATORY_ONLY")
            self.assertGreaterEqual(row["windows"], 1)
            self.assertIsInstance(row["mean_adaptive_return_fraction"], float)

    def test_provider_error_is_not_reported_as_success(self):
        def failing(ticker, period="2y"):
            if ticker == "NVDA":
                raise OSError("network unavailable")
            return fixture(ticker, period)
        report = summarize_research(run_historical_research(fetcher=failing))
        self.assertEqual(report["assets"]["NVDA"]["status"], "UNAVAILABLE")
        self.assertEqual(report["assets"]["SPY"]["status"], "EXPLORATORY_ONLY")


if __name__ == "__main__":
    unittest.main()
