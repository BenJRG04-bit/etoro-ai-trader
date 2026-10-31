import unittest
from holdout_risk_audit import audit_holdout
from run_holdout_report import run_holdout_report

def never_veto(prices):
    return {"regime_risk_veto": False}

class HoldoutRiskAuditTests(unittest.TestCase):
    def test_segments_are_disjoint_and_no_boundary_leak(self):
        prices = [100.0] * 200
        r = audit_holdout(prices, assessment_fn=never_veto)
        split = r["split_price_index"]
        self.assertEqual(split, 140)
        self.assertEqual(r["segments"]["earlier"]["horizons"]["20"]["non_veto"]["observations"], 61)
        self.assertEqual(r["segments"]["later_holdout"]["horizons"]["20"]["non_veto"]["observations"], 40)
        self.assertFalse(r["orders_allowed"])

    def test_signals_do_not_see_future(self):
        lengths = []
        def inspect(prices):
            lengths.append(len(prices))
            return {"regime_risk_veto": False}
        audit_holdout([100.0] * 200, horizons=(1,), assessment_fn=inspect)
        self.assertTrue(all(60 <= n <= 199 for n in lengths))

    def test_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            audit_holdout([100.0] * 159)
        with self.assertRaises(ValueError):
            audit_holdout([100.0] * 199 + [float("nan")])
        with self.assertRaises(ValueError):
            audit_holdout([100.0] * 200, holdout_fraction=0.1)
        with self.assertRaises(ValueError):
            audit_holdout([100.0] * 200, horizons=(1, 1))

    def test_empty_group_is_explicit(self):
        r = audit_holdout([100.0] * 200, assessment_fn=never_veto)
        self.assertIsNone(r["segments"]["later_holdout"]["horizons"]["1"]["veto"]["mean_forward_return_fraction"])

    def test_runner_uses_public_price_injection(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [str(i) for i in range(200)], "closes": [100.0] * 200}
        r = run_holdout_report(fetcher=fetch, tickers=("SPY",))
        self.assertEqual(r["assets"]["SPY"]["later_start_date"], "140")
        self.assertFalse(r["orders_allowed"])

    def test_runner_fails_closed(self):
        def fetch(ticker, period="2y"):
            raise ValueError("unavailable")
        r = run_holdout_report(fetcher=fetch, tickers=("SPY",))
        self.assertEqual(r["assets"]["SPY"]["status"], "UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
