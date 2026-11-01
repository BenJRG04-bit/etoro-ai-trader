import unittest
from forward_archive_integrity import validate_archived_snapshot
from historical_prices import WATCHLIST

class ArchiveIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.document = {"status": "SNAPSHOT_RESEARCH_ONLY",
                         "snapshot": {"schema_version": 1, "snapshot_date": "2026-10-30",
                                      "research_only": True, "orders_allowed": False,
                                      "live_trading_approved": False,
                                      "assets": {ticker: {"close": 100.0,
                                        "original_positive": False, "confirmed_positive": False,
                                        "risk_veto": True} for ticker in WATCHLIST}}}

    def test_valid_snapshot(self):
        self.assertEqual(validate_archived_snapshot(self.document)["snapshot_date"], "2026-10-30")

    def test_rejects_order_permission(self):
        self.document["snapshot"]["orders_allowed"] = True
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_missing_research_flag(self):
        self.document["snapshot"].pop("research_only")
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_nan_price(self):
        self.document["snapshot"]["assets"]["SPY"]["close"] = float("nan")
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_infinite_price(self):
        self.document["snapshot"]["assets"]["SPY"]["close"] = float("inf")
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_boolean_price(self):
        self.document["snapshot"]["assets"]["SPY"]["close"] = True
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_contradictory_veto(self):
        self.document["snapshot"]["assets"]["SPY"]["original_positive"] = True
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_nonboolean_signal(self):
        self.document["snapshot"]["assets"]["SPY"]["risk_veto"] = "false"
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_wrong_watchlist(self):
        self.document["snapshot"]["assets"].pop("SPY")
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

    def test_rejects_malformed_date(self):
        self.document["snapshot"]["snapshot_date"] = "2026-1-2"
        with self.assertRaises(ValueError):
            validate_archived_snapshot(self.document)

if __name__ == "__main__":
    unittest.main()
