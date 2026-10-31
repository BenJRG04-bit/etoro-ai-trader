import unittest
from run_diagnostic_report import run_diagnostic_report

class DiagnosticMarketReportTests(unittest.TestCase):
    @staticmethod
    def sample(ticker, period="2y"):
        return {"ticker": ticker, "closes": [100.0] * 100,
                "dates": ["2026-01-01", "2026-06-01"]}

    def test_offline_report(self):
        report = run_diagnostic_report(fetcher=self.sample, tickers=("SPY",))
        self.assertFalse(report["orders_allowed"])
        self.assertEqual(report["assets"]["SPY"]["diagnostics"]["evaluated_days"], 40)

    def test_missing_prices_never_fabricated(self):
        def unavailable(ticker, period="2y"):
            raise ValueError("unavailable")
        report = run_diagnostic_report(fetcher=unavailable, tickers=("SPY",))
        self.assertEqual(report["assets"]["SPY"]["status"], "UNAVAILABLE")
        self.assertNotIn("diagnostics", report["assets"]["SPY"])

    def test_wrong_ticker_rejected(self):
        def wrong(ticker, period="2y"):
            return {"ticker": "WRONG"}
        report = run_diagnostic_report(fetcher=wrong, tickers=("SPY",))
        self.assertEqual(report["assets"]["SPY"]["status"], "UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
