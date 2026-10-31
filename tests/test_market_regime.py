import unittest
from market_regime import classify_regime

class MarketRegimeTests(unittest.TestCase):
    def test_insufficient_data(self):
        self.assertEqual(classify_regime([100.0] * 59)["regime"], "INSUFFICIENT_DATA")
    def test_flat_is_sideways(self):
        self.assertEqual(classify_regime([100.0] * 80)["regime"], "SIDEWAYS")
    def test_steady_rise(self):
        self.assertEqual(classify_regime([100 + i * 0.2 for i in range(80)])["regime"], "UPTREND")
    def test_steep_drawdown_high_risk(self):
        self.assertEqual(classify_regime([100.0] * 60 + [70.0] * 20)["regime"], "HIGH_RISK")
    def test_bad_price(self):
        self.assertEqual(classify_regime([100.0] * 79 + [0.0])["regime"], "INSUFFICIENT_DATA")

if __name__ == "__main__":
    unittest.main()
