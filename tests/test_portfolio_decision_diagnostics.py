import unittest
from portfolio_decision_diagnostics import diagnose_portfolio_decisions
from run_portfolio_diagnostics import run_decision_diagnostics

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

def cautious(_):
    return {"status": "OK", "decision": "CAUTIOUS_RESEARCH", "regime_risk_veto": False}

class PortfolioDecisionDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"AAPL": [100. + i for i in range(80)],
                       "SPY": [200. + i for i in range(80)]}

    def test_positive_always_full_shared_target(self):
        result = diagnose_portfolio_decisions(self.prices, assessment_fn=positive)
        self.assertEqual(result["observed_decision_days"], 20)
        self.assertEqual(result["days_any_eligible"], 20)
        self.assertEqual(result["days_all_in_cash"], 0)
        self.assertEqual(result["portfolio_target_changes"], 1)
        self.assertEqual(result["max_total_target_exposure"], 0.05)
        self.assertFalse(result["orders_allowed"])

    def test_cautious_is_cash_and_misses_up_days_in_hindsight(self):
        result = diagnose_portfolio_decisions(self.prices, assessment_fn=cautious)
        self.assertEqual(result["days_all_in_cash"], 20)
        self.assertEqual(result["portfolio_target_changes"], 0)
        self.assertEqual(result["assets"]["AAPL"]["nonpositive_before_up_day"], 20)

    def test_signals_have_no_future_prices(self):
        seen = []
        def assessor(values):
            seen.append(len(values))
            return positive(values)
        diagnose_portfolio_decisions(self.prices, assessment_fn=assessor)
        self.assertEqual(seen[:2], [60, 60])
        self.assertEqual(max(seen), 79)

    def test_fee_estimate_on_one_entry(self):
        result = diagnose_portfolio_decisions(self.prices, fee_rate=0.005, assessment_fn=positive)
        self.assertAlmostEqual(result["approx_fee_fraction_of_starting_capital"], 0.00025)

    def test_reject_invalid_data(self):
        with self.assertRaises(ValueError):
            diagnose_portfolio_decisions({"AAPL": [100.] * 80, "SPY": [100.] * 79})
        with self.assertRaises(ValueError):
            diagnose_portfolio_decisions(self.prices, max_total_allocation=0.10)

    def test_runner_date_mismatch(self):
        def fetch(ticker, period="2y"):
            dates = [f"{i:03}" for i in range(80)]
            if ticker == "SPY":
                dates[3] = "999"
            return {"ticker": ticker, "dates": dates, "closes": [100.] * 80}
        self.assertEqual(run_decision_diagnostics(fetcher=fetch, tickers=("AAPL","SPY"))["status"], "UNAVAILABLE")

    def test_runner_success(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [f"{i:03}" for i in range(80)],
                    "closes": [100.] * 80}
        r = run_decision_diagnostics(fetcher=fetch, tickers=("AAPL","SPY"))
        self.assertEqual(r["status"], "EXPLORATORY_ONLY")
        self.assertEqual(r["diagnostics"]["days_all_in_cash"], 20)

if __name__ == "__main__":
    unittest.main()
