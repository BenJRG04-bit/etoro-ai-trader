import unittest
from adaptive_comparison import compare_regime_strategy
from backtest import backtest
from regime_council import regime_aware_council

class AdaptiveComparisonTests(unittest.TestCase):
    def test_flat_series(self):
        r = compare_regime_strategy([100.0] * 80)
        self.assertEqual(r["baseline"]["end_equity"], 1000.0)
        self.assertEqual(r["regime_aware"]["end_equity"], 1000.0)
        self.assertTrue(r["research_only"])

    def test_same_original_strategy(self):
        prices = [100 + i * .2 for i in range(100)]
        r = compare_regime_strategy(prices)
        self.assertEqual(r["baseline"], backtest(prices))

    def test_adaptive_uses_veto(self):
        prices = [100.0] * 60 + [70.0] * 20
        r = compare_regime_strategy(prices)
        self.assertEqual(r["regime_aware"], backtest(
            prices, assessment_fn=regime_aware_council))

    def test_reject_invalid_allocation(self):
        with self.assertRaises(ValueError):
            compare_regime_strategy([100.0] * 80, max_allocation=0.2)

if __name__ == "__main__":
    unittest.main()
