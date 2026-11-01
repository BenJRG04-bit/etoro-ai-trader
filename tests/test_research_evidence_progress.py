import unittest
from research_evidence_progress import summarize


class EvidenceProgressTests(unittest.TestCase):
    def sample(self, status="MORE_EVIDENCE_REQUIRED"):
        return {"status": status, "issues": ["HISTORY_COVERAGE_NOT_READY", "FORWARD_COVERAGE_NOT_READY"] if status == "MORE_EVIDENCE_REQUIRED" else [], "checks": {"history": {"status": "INSUFFICIENT_HISTORY"}, "forward": {"status": "INSUFFICIENT_FORWARD"}}, "research_only": True, "orders_allowed": False, "live_trading_approved": False}

    def test_pending_evidence_keeps_both_blockers(self):
        report = summarize(self.sample())
        self.assertEqual(len(report["blockers"]), 2)
        self.assertFalse(report["orders_allowed"])

    def test_ready_coverage_never_approves_trading(self):
        report = summarize(self.sample("RESEARCH_COVERAGE_READY"))
        self.assertFalse(report["live_trading_approved"])

    def test_rejects_missing_safety_flags(self):
        report = self.sample()
        del report["orders_allowed"]
        with self.assertRaises(ValueError):
            summarize(report)

    def test_rejects_unknown_status(self):
        with self.assertRaises(ValueError):
            summarize(self.sample("LIVE_APPROVED"))

    def test_rejects_bad_issues(self):
        report = self.sample()
        report["issues"] = "not a list"
        with self.assertRaises(ValueError):
            summarize(report)


if __name__ == "__main__":
    unittest.main()
