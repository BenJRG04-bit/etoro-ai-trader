"""Ensure price histories cannot be silently attributed to the wrong asset."""
import unittest
from datetime import date, timedelta
from historical_research_pipeline import run_historical_research


def sample(ticker, period="2y"):
    start = date(2023, 1, 1)
    return {
        "ticker": ticker,
        "price_type": "unadjusted_daily_close",
        "dates": [(start + timedelta(days=i)).isoformat() for i in range(180)],
        "closes": [100.0 + i / 10 for i in range(180)],
    }


class HistoricalResearchValidationTests(unittest.TestCase):
    def test_wrong_asset_is_rejected_not_misattributed(self):
        def wrong_asset(ticker, period="2y"):
            return sample("SPY", period)
        report = run_historical_research(fetcher=wrong_asset)
        self.assertEqual(report["assets"]["AAPL"]["status"],
                         "DATA_OR_EVALUATION_UNAVAILABLE")
        self.assertEqual(report["assets"]["SPY"]["status"], "EXPLORATORY_ONLY")
        self.assertFalse(report["live_trading_approved"])

    def test_unsupported_period_rejected(self):
        with self.assertRaises(ValueError):
            run_historical_research(fetcher=sample, period="all")

    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):
            run_historical_research(fetcher=sample, test_size=True)


if __name__ == "__main__":
    unittest.main()
