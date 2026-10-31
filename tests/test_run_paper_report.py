import unittest
from run_paper_report import run_report

class HistoricalPaperRunnerTests(unittest.TestCase):
    @staticmethod
    def fake_fetch(ticker, period="2y"):
        return {"ticker": ticker, "closes": [100.0] * 120,
                "dates": ["2026-01-01", "2026-06-01"],
                "price_type": "unadjusted_daily_close"}

    def test_report_is_offline_and_has_expected_asset(self):
        report = run_report(fetcher=self.fake_fetch, tickers=("SPY",))
        self.assertFalse(report["orders_allowed"])
        self.assertEqual(report["assets"]["SPY"]["status"], "EXPLORATORY_ONLY")
        self.assertEqual(report["assets"]["SPY"]["report"]["starting_cash"], 100.0)

    def test_fetch_error_does_not_make_fake_results(self):
        def fail(ticker, period="2y"):
            raise ValueError("no prices")
        report = run_report(fetcher=fail, tickers=("SPY",))
        self.assertEqual(report["assets"]["SPY"]["status"], "UNAVAILABLE")
        self.assertNotIn("report", report["assets"]["SPY"])

    def test_ticker_mismatch_rejected(self):
        def mismatch(ticker, period="2y"):
            return {"ticker": "OTHER"}
        report = run_report(fetcher=mismatch, tickers=("SPY",))
        self.assertEqual(report["assets"]["SPY"]["status"], "UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
