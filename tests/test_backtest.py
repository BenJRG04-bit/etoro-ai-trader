import unittest
from backtest import backtest

class BacktestTests(unittest.TestCase):
    def test_flat_prices(self):
        result = backtest([100.0] * 80)
        self.assertEqual(result["end_equity"], 1000.0)
        self.assertTrue(result["research_only"])
    def test_reject_bad_data(self):
        with self.assertRaises(ValueError):
            backtest([100.0] * 61 + [0.0])
    def test_allocation_cap(self):
        with self.assertRaises(ValueError):
            backtest([100.0] * 80, max_allocation=0.5)
    def test_output(self):
        result = backtest([100.0 + i for i in range(100)])
        self.assertGreater(result["end_equity"], 0)
        self.assertLessEqual(result["max_allocation"], 0.05)

if __name__ == "__main__":
    unittest.main()
