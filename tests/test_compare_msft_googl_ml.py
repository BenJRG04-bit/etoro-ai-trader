import unittest
from datetime import date, timedelta
from compare_msft_googl_ml import compare_candidates


class CandidateComparisonTests(unittest.TestCase):
    def test_both_candidates_assessed_without_orders(self):
        days = [(date(2024, 1, 1) + timedelta(days=i)).isoformat() for i in range(450)]
        def fetch(ticker, period="5y"):
            self.assertEqual(period, "5y")
            self.assertIn(ticker, ("MSFT", "GOOGL"))
            prices = [100 + 0.02*i + 2*(i % 7) for i in range(450)]
            return {"ticker": ticker, "dates": days, "closes": prices}
        report = compare_candidates(fetcher=fetch)
        self.assertEqual(set(report["candidates"]), {"MSFT", "GOOGL"})
        self.assertFalse(report["trade_authorized"])
        self.assertTrue(report["requires_walk_forward_validation"])
        self.assertFalse(report["model_probabilities_calibrated"])

    def test_data_failure_cannot_authorize_trading(self):
        def broken(ticker, period="5y"):
            raise ValueError("No history")
        report = compare_candidates(fetcher=broken)
        self.assertEqual(report["exploratory_shortlist"], [])
        self.assertFalse(report["trade_authorized"])
        self.assertFalse(report["candidates"]["MSFT"]["valid_holdout"])


if __name__ == "__main__":
    unittest.main()
