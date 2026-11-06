import unittest
from market_regime import classify_regime

class MarketRegimeTests(unittest.TestCase):
    def test_uptrend(self):
        self.assertEqual(classify_regime(list(range(1, 101)))["regime"], "UPTREND")
    def test_downtrend(self):
        self.assertEqual(classify_regime(list(range(100, 0, -1)))["regime"], "DOWNTREND")
    def test_sideways(self):
        self.assertEqual(classify_regime([100.0] * 100)["regime"], "SIDEWAYS")
    def test_insufficient_history(self):
        self.assertEqual(classify_regime([100.0] * 59)["regime"], "UNKNOWN")
    def test_bad_data(self):
        with self.assertRaises(ValueError):
            classify_regime([100.0] * 59 + [float("nan")])

if __name__ == "__main__":
    unittest.main()
