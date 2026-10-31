import unittest
from evidence_quality import assess_evidence_quality
from holdout_risk_audit import audit_holdout
from run_quality_report import run_quality_report

def no_veto(prices):
    return {"regime_risk_veto": False}

def always_veto(prices):
    return {"regime_risk_veto": True}

class EvidenceQualityTests(unittest.TestCase):
    def test_zero_veto_group_not_certified(self):
        audit = audit_holdout([100.0] * 200, assessment_fn=no_veto)
        quality = assess_evidence_quality(audit)
        self.assertFalse(quality["all_horizons_sample_adequate"])
        self.assertIn("later_holdout_veto_INSUFFICIENT_SAMPLE", quality["horizons"]["1"]["warnings"])
        self.assertFalse(quality["orders_allowed"])

    def test_zero_non_veto_group_not_certified(self):
        audit = audit_holdout([100.0] * 200, assessment_fn=always_veto)
        quality = assess_evidence_quality(audit)
        self.assertFalse(quality["all_horizons_sample_adequate"])

    def test_rejects_invalid_minimum(self):
        audit = audit_holdout([100.0] * 200, assessment_fn=no_veto)
        for value in (0, 5, True, 2.5):
            with self.assertRaises(ValueError):
                assess_evidence_quality(audit, min_signals_per_group=value)

    def test_rejects_invalid_mean(self):
        audit = audit_holdout([100.0] * 200, assessment_fn=no_veto)
        audit["segments"]["earlier"]["horizons"]["1"]["non_veto"]["mean_forward_return_fraction"] = float("nan")
        with self.assertRaises(ValueError):
            assess_evidence_quality(audit)

    def test_report_no_market_data(self):
        def missing(ticker, period="2y"):
            raise ValueError("No data")
        r = run_quality_report(fetcher=missing, tickers=("SPY",))
        self.assertEqual(r["assets"]["SPY"]["status"], "UNAVAILABLE")
        self.assertFalse(r["orders_allowed"])

    def test_report_with_mock_prices(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [str(x) for x in range(200)], "closes": [100.0] * 200}
        r = run_quality_report(fetcher=fetch, tickers=("SPY",))
        self.assertFalse(r["assets"]["SPY"]["sample_adequate"])
        self.assertEqual(r["assets"]["SPY"]["split_date"], "140")

if __name__ == "__main__":
    unittest.main()
