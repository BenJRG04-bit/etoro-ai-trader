import unittest
from copy import deepcopy
from archive_freshness import assess_archive_freshness

class ArchiveFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.history = {"status": "RESEARCH_ACCOUNTABILITY_HISTORY", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "selected_report_dates": 1, "last_date": "2026-10-30",
            "timeline": [{"date": "2026-10-30"}]}
        self.forward = {"status": "RESEARCH_AUDIT", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "snapshot_count": 1, "results": [{"snapshot_date": "2026-10-29"}]}

    def check(self):
        return assess_archive_freshness(self.history, self.forward, as_of="2026-11-01")

    def test_recent_archives(self):
        result = self.check()
        self.assertEqual(result["status"], "ARCHIVES_CURRENT")
        self.assertFalse(result["orders_allowed"])

    def test_old_history(self):
        self.history["timeline"][0]["date"] = self.history["last_date"] = "2026-10-01"
        self.assertIn("HISTORY_MISSING_OR_STALE", self.check()["issues"])

    def test_old_forward(self):
        self.forward["results"][0]["snapshot_date"] = "2026-10-01"
        self.assertIn("FORWARD_MISSING_OR_STALE", self.check()["issues"])

    def test_empty_archives(self):
        self.history.update(selected_report_dates=0, last_date=None, timeline=[])
        self.forward.update(snapshot_count=0, results=[])
        self.assertEqual(len(self.check()["issues"]), 2)

    def test_rejects_future_date(self):
        self.history["timeline"][0]["date"] = self.history["last_date"] = "2026-11-02"
        with self.assertRaises(ValueError):
            self.check()

    def test_rejects_unsafe_archive(self):
        self.forward["orders_allowed"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_rejects_mismatched_count(self):
        self.forward["snapshot_count"] = 2
        with self.assertRaises(ValueError):
            self.check()

    def test_rejects_duplicate_dates(self):
        self.history["timeline"].append(deepcopy(self.history["timeline"][0]))
        self.history["selected_report_dates"] = 2
        with self.assertRaises(ValueError):
            self.check()

    def test_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            assess_archive_freshness(self.history, self.forward, as_of="2026-11-01",
                                     maximum_history_age_days=-1)

if __name__ == "__main__":
    unittest.main()
