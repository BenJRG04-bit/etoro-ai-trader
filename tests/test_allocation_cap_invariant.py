import unittest
from portfolio_simulator import simulate_portfolio

def shifting_signal(series):
    # A becomes ineligible at day 61 while B becomes eligible.
    is_b = series[0] == 200
    eligible = (is_b and len(series) >= 61) or (not is_b and len(series) < 61)
    return {"status": "OK", "regime_risk_veto": False,
            "decision": "POSITIVE_RESEARCH" if eligible else "WAIT_RESEARCH"}

class AllocationCapInvariantTests(unittest.TestCase):
    def test_minimum_order_skipped_sale_never_causes_overallocation(self):
        prices = {"A": [100.] * 70, "B": [200.] * 70}
        # At £100, a £5 sale is skipped if minimum order > £5,
        # but new £5 buy would also be skipped. Force partial sale vs buy:
        # two old eligible positions with unequal desired changes.
        result = simulate_portfolio(prices, assessment_fn=shifting_signal,
                                    starting_cash=100, minimum_order=6)
        self.assertLessEqual(result["max_observed_total_allocation"], .05)
        self.assertFalse(result["orders_allowed"])
    def test_costs_cannot_exceed_full_turnover(self):
        with self.assertRaises(ValueError):
            simulate_portfolio({"A": [100.] * 70},
                               fee_rate=.8, spread_rate=.8, slippage_rate=.1, fx_rate=.1)
    def test_regular_costs_remain_supported(self):
        result = simulate_portfolio({"A": [100.] * 70},
                                    fee_rate=.001, spread_rate=.001, minimum_order=1)
        self.assertLessEqual(result["max_observed_total_allocation"], .05)
