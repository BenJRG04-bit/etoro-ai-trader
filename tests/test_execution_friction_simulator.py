import unittest
from portfolio_simulator import simulate_portfolio

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

class ExecutionFrictionSimulationTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"A": [100 + i * .1 for i in range(85)]}
    def test_extra_costs_reduce_equity(self):
        base = simulate_portfolio(self.prices, assessment_fn=positive)
        costly = simulate_portfolio(self.prices, assessment_fn=positive, spread_rate=.01, slippage_rate=.01, fx_rate=.01)
        self.assertLess(costly["end_equity"], base["end_equity"])
    def test_minimum_prevents_small_orders(self):
        result = simulate_portfolio(self.prices, starting_cash=20, assessment_fn=positive, minimum_order=10)
        self.assertEqual(result["rebalance_events"], 0)
        self.assertEqual(result["end_equity"], 20)
    def test_five_percent_cap_preserved(self):
        result = simulate_portfolio(self.prices, assessment_fn=positive, spread_rate=.005)
        self.assertLessEqual(result["max_observed_total_allocation"], .05)
        self.assertFalse(result["orders_allowed"])
    def test_invalid_friction_rejected(self):
        with self.assertRaises(ValueError):
            simulate_portfolio(self.prices, fx_rate=float("nan"))
        with self.assertRaises(ValueError):
            simulate_portfolio(self.prices, minimum_order=-1)
