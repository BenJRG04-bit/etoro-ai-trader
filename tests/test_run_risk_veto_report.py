import unittest
from run_risk_veto_report import run_risk_veto_report

class RiskVetoReportTests(unittest.TestCase):
    def test_sample_report(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "closes": [100.0] * 80,
                    "dates": ["2026-01-01", "2026-05-01"]}
        result = run_risk_veto_report(fetcher=fetch, tickers=("SPY",))
        self.assertEqual(result["assets"]["SPY"]["outcomes"]["other_days"]["days"], 20)
        self.assertFalse(result["orders_allowed"])

    def test_unavailable_prices(self):
        def fetch(ticker, period="2y"):
            raise ValueError("No data")
        result = run_risk_veto_report(fetcher=fetch, tickers=("SPY",))
        self.assertEqual(result["assets"]["SPY"]["status"], "UNAVAILABLE")

    def test_ticker_mismatch(self):
        def fetch(ticker, period="2y"):
            return {"ticker": "OTHER"}
        result = run_risk_veto_report(fetcher=fetch, tickers=("SPY",))
        self.assertEqual(result["assets"]["SPY"]["status"], "UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
