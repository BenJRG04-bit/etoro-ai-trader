import unittest
from decision_confirmation_experiment import confirmed_assessment, compare_confirmation
from run_confirmation_report import run_confirmation_report

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

def veto(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": True}

class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"AAPL": [100. + i for i in range(80)],
                       "SPY": [200. + i for i in range(80)]}

    def test_confirmation_needs_two_positive_closes(self):
        def assessor(closes):
            return positive(closes) if len(closes) >= 60 else {
                "status": "OK", "decision": "CAUTIOUS_RESEARCH", "regime_risk_veto": False}
        self.assertEqual(confirmed_assessment([100.] * 60, assessor)["decision"], "WAIT_FOR_CONFIRMATION")
        self.assertEqual(confirmed_assessment([100.] * 61, assessor)["decision"], "POSITIVE_RESEARCH")

    def test_veto_is_never_delayed(self):
        self.assertTrue(confirmed_assessment([100.] * 60, veto)["regime_risk_veto"])

    def test_does_not_look_forward(self):
        seen = []
        def assessor(closes):
            seen.append(len(closes))
            return positive(closes)
        confirmed_assessment([100.] * 60, assessor)
        self.assertEqual(seen, [60, 59])

    def test_comparison_respects_cap_and_no_orders(self):
        r = compare_confirmation(self.prices, base_assessment=positive)
        for row in r["scenarios"].values():
            for policy in ("existing_council", "two_close_confirmation"):
                self.assertLessEqual(row[policy]["max_observed_total_allocation"], 0.05)
                self.assertFalse(row[policy]["orders_allowed"])

    def test_reject_empty_fee_scenarios(self):
        with self.assertRaises(ValueError):
            compare_confirmation(self.prices, fee_rates=())

    def test_runner_rejects_date_mismatch(self):
        def fetch(ticker, period="2y"):
            dates = [f"{i:03}" for i in range(80)]
            if ticker == "SPY":
                dates[4] = "999"
            return {"ticker": ticker, "dates": dates, "closes": [100.] * 80}
        self.assertEqual(run_confirmation_report(fetcher=fetch, tickers=("AAPL", "SPY"))["status"], "UNAVAILABLE")

    def test_runner_success(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [f"{i:03}" for i in range(80)],
                    "closes": [100. + i for i in range(80)]}
        r = run_confirmation_report(fetcher=fetch, tickers=("AAPL", "SPY"))
        self.assertEqual(r["status"], "EXPLORATORY_ONLY")
        self.assertFalse(r["orders_allowed"])

if __name__ == "__main__":
    unittest.main()
