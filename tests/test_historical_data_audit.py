import unittest
from historical_data_audit import audit_history


def sample():
    from datetime import date, timedelta
    start = date(2024, 1, 1)
    return {
        "ticker": "SPY",
        "price_type": "unadjusted_daily_close",
        "dates": [(start + timedelta(days=i)).isoformat()
                  for i in range(120)],
        "closes": [100.0 + i for i in range(120)],
    }


class HistoricalDataAuditTests(unittest.TestCase):
    def test_valid_data_still_blocks_total_return_claims(self):
        result = audit_history(sample())
        self.assertEqual(result["observation_count"], 120)
        self.assertTrue(result["valid_for_exploratory_research"])
        self.assertFalse(result["valid_for_total_return_comparison"])
        self.assertFalse(result["live_trading_approved"])

    def test_duplicate_dates_rejected(self):
        data = sample()
        data["dates"][1] = data["dates"][0]
        with self.assertRaises(ValueError):
            audit_history(data)

    def test_missing_price_rejected(self):
        data = sample()
        data["closes"][10] = None
        with self.assertRaises(ValueError):
            audit_history(data)

    def test_unrecognized_price_type_rejected(self):
        data = sample()
        data["price_type"] = "adjusted"
        with self.assertRaises(ValueError):
            audit_history(data)


if __name__ == "__main__":
    unittest.main()
