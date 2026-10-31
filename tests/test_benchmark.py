import unittest
from benchmark import compare_to_buy_and_hold

class BenchmarkTests(unittest.TestCase):
    def test_flat_prices(self):
        result = compare_to_buy_and_hold([100.0] * 80)
        self.assertEqual(result["benchmark_end_equity"], 999.95)
        self.assertEqual(result["strategy"]["end_equity"], 1000.0)
        self.assertTrue(result["research_only"])

    def test_zero_allocation(self):
        result = compare_to_buy_and_hold([100.0 + i for i in range(80)],
                                         max_allocation=0)
        self.assertEqual(result["benchmark_end_equity"], 1000.0)

    def test_invalid_prices(self):
        with self.assertRaises(ValueError):
            compare_to_buy_and_hold([100.0] * 61 + [0.0])

if __name__ == "__main__":
    unittest.main()
