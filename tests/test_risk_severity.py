import unittest
from risk_severity import evaluate_risk_severity
from run_severity_report import run_severity_report

def veto(prices):
    return {"regime_risk_veto": prices[-1] < 90}

class RiskSeverityTests(unittest.TestCase):
    def test_flat_prices_and_horizons(self):
        r = evaluate_risk_severity([100.0] * 100, assessment_fn=veto)
        self.assertEqual(r["signal_days"]["non_veto"], 40)
        self.assertEqual(r["horizons"]["1"]["non_veto"]["observations"], 40)
        self.assertEqual(r["horizons"]["20"]["non_veto"]["observations"], 21)
        self.assertEqual(r["horizons"]["5"]["non_veto"]["worst_return_fraction"], 0)
        self.assertFalse(r["orders_allowed"])

    def test_veto_loss_severity(self):
        prices = [100.0] * 60 + [80.0] * 30
        r = evaluate_risk_severity(prices, horizons=(1, 5), assessment_fn=veto)
        self.assertGreater(r["signal_days"]["veto"], 0)
        self.assertEqual(r["horizons"]["1"]["non_veto"]["loss_at_least_5pct_count"], 1)
        self.assertEqual(r["horizons"]["1"]["veto"]["loss_at_least_5pct_count"], 0)

    def test_no_lookahead_in_signal(self):
        lengths = []
        def inspect(prices):
            lengths.append(len(prices))
            return {"regime_risk_veto": False}
        evaluate_risk_severity([100.0] * 75, horizons=(1,), assessment_fn=inspect)
        self.assertEqual(lengths, list(range(60, 75)))

    def test_invalid_input(self):
        for prices in ([100.0] * 61, [100.0] * 70 + [float("nan")], [100.0] * 70 + [False]):
            with self.assertRaises(ValueError):
                evaluate_risk_severity(prices)
        with self.assertRaises(ValueError):
            evaluate_risk_severity([100.0] * 80, horizons=(1, 1))

    def test_report_failure_is_explicit(self):
        def unavailable(ticker, period="2y"):
            raise ValueError("No prices")
        r = run_severity_report(fetcher=unavailable, tickers=("SPY",))
        self.assertEqual(r["assets"]["SPY"]["status"], "UNAVAILABLE")
        self.assertFalse(r["orders_allowed"])

    def test_report_with_prices(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "closes": [100.0] * 80, "dates": ["day"] * 80}
        r = run_severity_report(fetcher=fetch, tickers=("SPY",))
        self.assertEqual(r["assets"]["SPY"]["severity"]["horizons"]["1"]["non_veto"]["observations"], 20)

if __name__ == "__main__":
    unittest.main()
