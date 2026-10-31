import unittest
from research_strategy_selector import research_strategy_selection

class ResearchStrategySelectorTests(unittest.TestCase):
    def test_missing_history_never_selects(self):
        result = research_strategy_selection([100.0] * 59)
        self.assertEqual(result["candidate_strategies"], [])
        self.assertFalse(result["orders_allowed"])

    def test_crash_withholds_directional_candidates(self):
        result = research_strategy_selection([100.0] * 60 + [70.0] * 20)
        self.assertEqual(result["market_regime"], "HIGH_RISK")
        self.assertEqual(result["candidate_strategies"], [])
        self.assertFalse(result["live_trading_approved"])

    def test_flat_market_comparison_only(self):
        result = research_strategy_selection([100.0] * 80)
        self.assertIn("buy_and_hold_benchmark", result["candidate_strategies"])
        self.assertTrue(result["research_only"])

    def test_invalid_price_never_selects(self):
        result = research_strategy_selection([100.0] * 79 + [0.0])
        self.assertEqual(result["candidate_strategies"], [])
        self.assertFalse(result["orders_allowed"])

if __name__ == "__main__":
    unittest.main()
