import unittest
from paper_performance_report import paper_performance_report

class PaperPerformanceReportTests(unittest.TestCase):
    def test_flat_prices(self):
        r = paper_performance_report([100.0] * 80)
        self.assertEqual(r["strategy_end"], 100.0)
        self.assertLess(r["benchmark_end"], 100.0)
        self.assertFalse(r["live_trading_approved"])

    def test_crash_stays_offline(self):
        r = paper_performance_report([100.0] * 60 + [70.0] * 20)
        self.assertEqual(r["strategy"]["mode"], "HISTORICAL_PAPER_ACCOUNT_NO_ORDERS")
        self.assertFalse(r["strategy"]["orders_allowed"])

    def test_short_history_rejected(self):
        with self.assertRaises(ValueError):
            paper_performance_report([100.0] * 20)

    def test_bad_price_rejected(self):
        with self.assertRaises(ValueError):
            paper_performance_report([100.0] * 79 + [float("nan")])

if __name__ == "__main__":
    unittest.main()
