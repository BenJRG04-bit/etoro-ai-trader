import unittest
from friction_stress_test import friction_backtest, compare_friction_scenarios

def always_positive(closes):
    return {"decision": "POSITIVE_RESEARCH"}

class FrictionStressTests(unittest.TestCase):
    def test_flat_prices_costs_reduce_equity(self):
        result = friction_backtest([100.0] * 80, assessment_fn=always_positive)
        self.assertLess(result["end_equity"], 1000)
        self.assertGreater(result["estimated_friction_paid"], 0)

    def test_more_friction_worse_when_positions_identical(self):
        prices = [100.0] * 80
        cheap = friction_backtest(prices, assessment_fn=always_positive,
                                  commission_rate=0, spread_rate=0, slippage_rate=0)
        costly = friction_backtest(prices, assessment_fn=always_positive,
                                   commission_rate=.003, spread_rate=.006, slippage_rate=.003)
        self.assertGreater(cheap["end_equity"], costly["end_equity"])

    def test_no_allocation_no_friction(self):
        result = friction_backtest([100.0] * 80, assessment_fn=always_positive,
                                   max_allocation=0)
        self.assertEqual(result["end_equity"], 1000)
        self.assertEqual(result["rebalance_events"], 0)

    def test_reject_oversized_allocation(self):
        with self.assertRaises(ValueError):
            friction_backtest([100.0] * 80, max_allocation=.5)

    def test_scenarios_research_only(self):
        result = compare_friction_scenarios([100.0] * 80)
        self.assertEqual(set(result["scenarios"]), {"optimistic", "moderate", "pessimistic"})
        self.assertTrue(result["research_only"])

if __name__ == "__main__":
    unittest.main()
