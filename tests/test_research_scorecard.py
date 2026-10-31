import unittest
from research_scorecard import research_scorecard


class ResearchScorecardTests(unittest.TestCase):
    def test_flat_market_and_no_live_approval(self):
        result = research_scorecard([100.0] * 80)
        self.assertTrue(result["research_only"])
        self.assertFalse(result["live_trading_approved"])
        self.assertEqual(result["mode"], "OFFLINE_RESEARCH_SCORECARD_NO_ORDERS")
        self.assertEqual(result["capped_buy_and_hold"]["end_equity"], 999.95)
        self.assertIsNone(result["capped_buy_and_hold"]["max_drawdown_fraction"])

    def test_zero_allocation(self):
        result = research_scorecard([100.0 + i for i in range(80)],
                                    max_allocation=0)
        for key in ("baseline", "regime_aware", "capped_buy_and_hold"):
            self.assertEqual(result[key]["end_equity"], 1000.0)

    def test_invalid_data_rejected(self):
        with self.assertRaises(ValueError):
            research_scorecard([100.0] * 61 + [0.0])


if __name__ == "__main__":
    unittest.main()
