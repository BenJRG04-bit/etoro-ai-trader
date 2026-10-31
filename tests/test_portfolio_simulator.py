import unittest
from portfolio_simulator import simulate_portfolio
from run_portfolio_report import run_portfolio_report

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

def veto(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": True}

class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"AAPL": [100.0 + i for i in range(80)], "SPY": [200.0 + i for i in range(80)]}

    def test_shared_cap_not_per_asset(self):
        r = simulate_portfolio(self.prices, assessment_fn=positive)
        self.assertLessEqual(r["max_observed_total_allocation"], 0.05)
        self.assertEqual(r["max_observed_total_allocation"], 0.05)
        self.assertFalse(r["orders_allowed"])
        self.assertEqual(r["starting_cash"], 100.0)

    def test_veto_leaves_cash(self):
        r = simulate_portfolio(self.prices, assessment_fn=veto)
        self.assertEqual(r["end_equity"], 100.0)
        self.assertEqual(r["rebalance_events"], 0)

    def test_no_future_prices_in_decision(self):
        seen = []
        def assessor(prices):
            seen.append(len(prices))
            return positive(prices)
        simulate_portfolio(self.prices, assessment_fn=assessor)
        self.assertEqual(seen[:2], [60, 60])
        self.assertEqual(max(seen), 79)

    def test_fee_costs_reduce_value(self):
        cheap = simulate_portfolio(self.prices, fee_rate=0, assessment_fn=positive)
        costly = simulate_portfolio(self.prices, fee_rate=0.005, assessment_fn=positive)
        self.assertLess(costly["end_equity"], cheap["end_equity"])

    def test_rejects_invalid_inputs(self):
        bad = ({"SPY": [100.0] * 61}, {"SPY": [100.0] * 80, "AAPL": [100.0] * 79},
               {"SPY": [100.0] * 79 + [0.0]})
        for prices in bad:
            with self.assertRaises(ValueError):
                simulate_portfolio(prices)
        with self.assertRaises(ValueError):
            simulate_portfolio(self.prices, max_total_allocation=0.06)

    def test_runner_rejects_misaligned_dates(self):
        def fetch(ticker, period="2y"):
            dates = [str(i) for i in range(80)]
            if ticker == "SPY":
                dates[5] = "changed"
            return {"ticker": ticker, "dates": dates, "closes": [100.0] * 80}
        r = run_portfolio_report(fetcher=fetch, tickers=("AAPL", "SPY"))
        self.assertEqual(r["status"], "UNAVAILABLE")
        self.assertFalse(r["orders_allowed"])

    def test_runner_with_synchronized_dates(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [f"{i:03}" for i in range(80)], "closes": [100.0] * 80}
        r = run_portfolio_report(fetcher=fetch, tickers=("AAPL", "SPY"))
        self.assertEqual(r["status"], "EXPLORATORY_ONLY")
        self.assertEqual(r["simulation"]["max_observed_total_allocation"], 0.0)

    def test_runner_no_data(self):
        r = run_portfolio_report(tickers=())
        self.assertEqual(r["status"], "UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
