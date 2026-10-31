import unittest
from forward_batch_audit import audit_forward_snapshots
from run_forward_batch_audit import run_batch
from historical_prices import WATCHLIST

class BatchAuditTests(unittest.TestCase):
    def setUp(self):
        self.dates = [f"2025-{1+i//28:02}-{1+i%28:02}" for i in range(70)]
        self.calls = []
    def doc(self, index=68):
        return {"status": "SNAPSHOT_RESEARCH_ONLY",
                "snapshot": {"schema_version": 1, "research_only": True,
                             "snapshot_date": self.dates[index],
                             "assets": {t: {"close": 100., "original_positive": True,
                                           "confirmed_positive": False, "risk_veto": False}
                                        for t in WATCHLIST}}}
    def fetch(self, ticker, period="2y"):
        self.calls.append(ticker)
        return {"ticker": ticker, "dates": self.dates, "closes": [100.] * 69 + [101.]}

    def test_observed_and_pending(self):
        r = audit_forward_snapshots([self.doc(68), self.doc(69)], self.fetch)
        self.assertEqual(r["observed_snapshots"], 1)
        self.assertEqual(r["pending_snapshots"], 1)
        self.assertFalse(r["orders_allowed"])

    def test_duplicates_do_not_double_count(self):
        r = audit_forward_snapshots([self.doc(), self.doc()], self.fetch)
        self.assertEqual(r["snapshot_count"], 1)

    def test_conflicting_snapshots_excluded(self):
        conflict = self.doc()
        conflict["snapshot"]["assets"]["AAPL"]["close"] = 105.
        r = audit_forward_snapshots([self.doc(), conflict], self.fetch)
        self.assertEqual(r["snapshot_count"], 0)
        self.assertEqual(r["rejected_snapshots"], 1)

    def test_malformed_snapshot_rejected(self):
        r = audit_forward_snapshots([{}, self.doc()], self.fetch)
        self.assertEqual(r["rejected_snapshots"], 1)

    def test_limit_restricts_dates(self):
        r = audit_forward_snapshots([self.doc(67), self.doc(68)], self.fetch, max_snapshots=1)
        self.assertEqual(r["snapshot_count"], 1)
        self.assertEqual(r["results"][0]["snapshot_date"], self.dates[68])

    def test_invalid_limit_rejected(self):
        with self.assertRaises(ValueError):
            audit_forward_snapshots([], self.fetch, max_snapshots=0)

    def test_caches_one_fetch_per_asset(self):
        r = run_batch([], self.fetch)
        self.assertEqual(r["status"], "RESEARCH_AUDIT")
        self.assertEqual(len(self.calls), len(WATCHLIST))

    def test_does_not_count_pending_as_wins(self):
        r = audit_forward_snapshots([self.doc(69)], self.fetch)
        self.assertEqual(r["results"][0]["positive_signals"]["original"]["count"], 0)

if __name__ == "__main__":
    unittest.main()
