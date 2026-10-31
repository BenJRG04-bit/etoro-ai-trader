import unittest
from regime_council import regime_aware_council
from six_brains import council

class RegimeCouncilTests(unittest.TestCase):
    def test_missing_data(self):
        result = regime_aware_council([100.0] * 59)
        self.assertEqual(result["decision"], "NO_ASSESSMENT")
        self.assertFalse(result["regime_risk_veto"])

    def test_high_risk_veto(self):
        prices = [100.0] * 60 + [70.0] * 20
        result = regime_aware_council(prices)
        self.assertEqual(result["market_regime"], "HIGH_RISK")
        self.assertEqual(result["decision"], "CAUTIOUS_RESEARCH")
        self.assertTrue(result["regime_risk_veto"])

    def test_normal_regime_preserves_council(self):
        prices = [100.0 + i * 0.2 for i in range(80)]
        result = regime_aware_council(prices)
        self.assertEqual(result["decision"], council(prices)["decision"])
        self.assertFalse(result["regime_risk_veto"])

    def test_never_places_orders(self):
        result = regime_aware_council([100.0] * 80)
        self.assertTrue(result["research_only"])

if __name__ == "__main__":
    unittest.main()
