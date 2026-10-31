import unittest
from historical_evaluation import evaluate_windows

class HistoricalEvaluationTests(unittest.TestCase):
    def test_nonoverlapping_windows(self):
        prices = [100 + 0.1 * i for i in range(180)]
        r = evaluate_windows(prices, test_size=60)
        self.assertEqual(r["window_count"], 2)
        self.assertEqual([(w["test_start_index"], w["test_end_index_exclusive"])
                          for w in r["windows"]], [(60, 120), (120, 180)])
        self.assertTrue(r["research_only"])

    def test_short_data_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_windows([100.0] * 119, test_size=60)

    def test_invalid_prices_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_windows([100.0] * 119 + [float("nan")])

    def test_allocation_cap(self):
        with self.assertRaises(ValueError):
            evaluate_windows([100.0] * 120, max_allocation=0.5)

if __name__ == "__main__":
    unittest.main()
