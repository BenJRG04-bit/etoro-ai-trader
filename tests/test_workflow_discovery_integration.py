import unittest
from run_workflow_diagnostics import run_diagnostics
from workflow_run_diagnostics import WORKFLOWS
from workflow_diagnostics_dashboard import render_pipeline_dashboard

class WorkflowDiscoveryIntegrationTests(unittest.TestCase):
    def test_queries_each_workflow_not_global_recent_runs(self):
        urls = []
        def fetch(url, headers):
            urls.append(url)
            filename = url.split("/workflows/")[1].split("/runs")[0]
            return {"workflow_runs": [{"id": 10, "created_at": "2026-11-01T00:00:00Z",
                "head_branch": "main", "status": "completed", "conclusion": "success",
                "event": "schedule"}]}
        result = run_diagnostics("owner/repo", "test-token", fetch=fetch)
        self.assertEqual(len(urls), len(WORKFLOWS))
        self.assertTrue(all("/actions/workflows/" in url for url in urls))
        self.assertTrue(all("/runs?branch=main" in url for url in urls))
        self.assertEqual(set(result["workflows"]), set(WORKFLOWS.values()))

    def test_one_api_failure_blocks_health_and_renders(self):
        def fetch(url, headers):
            if "council-history.yml" in url:
                raise OSError("temporary unavailable")
            return {"workflow_runs": []}
        result = run_diagnostics("owner/repo", "test-token", fetch=fetch)
        self.assertEqual(result["workflows"]["archived_council_history"]["status"], "FETCH_ERROR")
        self.assertEqual(result["status"], "WORKFLOW_VERIFICATION_INCOMPLETE")
        self.assertIn("FETCH_ERROR", render_pipeline_dashboard(result))

    def test_partial_valid_data_does_not_hide_api_error(self):
        def fetch(url, headers):
            if "research-readiness.yml" in url:
                return {"bad": "payload"}
            return {"workflow_runs": []}
        result = run_diagnostics("owner/repo", "test-token", fetch=fetch)
        self.assertIn("combined_readiness", result["blockers"])

    def test_rejects_bad_repo(self):
        with self.assertRaises(ValueError):
            run_diagnostics("invalid", "test-token", fetch=lambda u, h: {})

if __name__ == "__main__":
    unittest.main()
