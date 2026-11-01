import unittest
from datetime import datetime, timezone
from workflow_run_diagnostics import summarize_workflow_runs
from run_workflow_diagnostics import run_diagnostics

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
def row(path, *, created="2026-11-01T10:00:00Z", status="completed", conclusion="success"):
    return {"path": ".github/workflows/" + path, "head_branch": "main", "created_at": created,
            "status": status, "conclusion": conclusion, "id": 12, "event": "schedule"}

class WorkflowDiagnosticsTests(unittest.TestCase):
    def test_empty_runs_not_verified(self):
        result = summarize_workflow_runs([], now=NOW)
        self.assertEqual(result["status"], "WORKFLOW_VERIFICATION_INCOMPLETE")
        self.assertEqual(len(result["blockers"]), 5)

    def test_all_five_successful(self):
        names = ["council-accountability.yml", "council-history.yml", "forward-signals.yml",
                 "forward-batch-audit.yml", "research-readiness.yml"]
        result = summarize_workflow_runs([row(name) for name in names], now=NOW)
        self.assertEqual(result["status"], "WORKFLOW_RUNS_PRESENT")
        self.assertFalse(result["orders_allowed"])

    def test_stale_run(self):
        result = summarize_workflow_runs([row("council-history.yml", created="2026-10-01T10:00:00Z")], now=NOW)
        self.assertEqual(result["workflows"]["archived_council_history"]["status"], "STALE_RUN")

    def test_failed_run(self):
        result = summarize_workflow_runs([row("council-history.yml", conclusion="failure")], now=NOW)
        self.assertEqual(result["workflows"]["archived_council_history"]["status"], "INCOMPLETE_OR_FAILED")

    def test_wrong_branch_ignored(self):
        item = row("council-history.yml")
        item["head_branch"] = "feature"
        self.assertEqual(summarize_workflow_runs([item], now=NOW)["workflows"]["archived_council_history"]["status"], "NO_RUN_FOUND")

    def test_future_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            summarize_workflow_runs([row("council-history.yml", created="2026-11-02T10:00:00Z")], now=NOW)

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            summarize_workflow_runs([], now=NOW, max_age_hours=0)

    def test_fetcher_injection(self):
        result = run_diagnostics("owner/repo", "test-token",
            fetch=lambda url, headers: {"workflow_runs": []})
        self.assertEqual(result["status"], "WORKFLOW_VERIFICATION_INCOMPLETE")

    def test_rejects_malformed_response(self):
        with self.assertRaises(ValueError):
            run_diagnostics("owner/repo", "test-token", fetch=lambda url, headers: {})

if __name__ == "__main__":
    unittest.main()
