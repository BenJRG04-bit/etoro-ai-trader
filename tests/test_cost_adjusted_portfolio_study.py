import unittest
from cost_adjusted_portfolio_study import compare_cost_assumptions

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

class CostAdjustedStudyTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"A": [100 + i*.2 for i in range(85)]}
    def test_three_budgets_three_cost_scenarios(self):
        report = compare_cost_assumptions(self.prices, assessment_fn=positive)
        self.assertEqual(set(report["budgets"]), {"20", "40", "100"})
        self.assertEqual(len(report["budgets"]["20"]), 3)
        self.assertFalse(report["orders_allowed"])
    def test_extra_friction_reduces_equity_when_orders_possible(self):
        result = compare_cost_assumptions(self.prices, budgets=(100,), assessment_fn=positive)
        cases = result["budgets"]["100"]
        self.assertLess(cases["illustrative_friction"]["ending_equity"], cases["base_fees_only"]["ending_equity"])
    def test_high_minimum_blocks_trading(self):
        cases = compare_cost_assumptions(self.prices, budgets=(20,), assessment_fn=positive)["budgets"]["20"]
        self.assertEqual(cases["high_friction"]["rebalance_events"], 0)
    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            compare_cost_assumptions(self.prices, budgets=(0,))
    def test_invalid_scenario_parameter(self):
        with self.assertRaises(ValueError):
            compare_cost_assumptions(self.prices, assumptions={"base_fees_only": {"unknown": 1}})
