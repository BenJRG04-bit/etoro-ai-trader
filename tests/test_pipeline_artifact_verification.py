import unittest
from workflow_run_diagnostics import summarize_workflow_runs, WORKFLOWS
from pipeline_artifact_verification import verify_pipeline_artifacts, EXPECTED_ARTIFACTS
from workflow_diagnostics_dashboard import render_pipeline_dashboard

def all_success():
    report = summarize_workflow_runs([])
    for label, item in report["workflows"].items():
        item.update(status="SUCCESS", run_id=12)
    report["status"] = "WORKFLOW_RUNS_PRESENT"
    report["blockers"] = []
    return report

class ArtifactVerificationTests(unittest.TestCase):
    def test_present_artifacts(self):
        report = all_success()
        def fetch(url, headers):
            label = next(k for k, v in EXPECTED_ARTIFACTS.items() if v in headers["expected_names"])
            return {"artifacts": [{"name": EXPECTED_ARTIFACTS[label], "expired": False, "size_in_bytes": 100}]}
        # Different workflow IDs are required to disambiguate expected artifacts.
        for i, label in enumerate(EXPECTED_ARTIFACTS, start=1):
            report["workflows"][label]["run_id"] = i
        def fetch_by_run(url, headers):
            number = int(url.split("/actions/runs/")[1].split("/")[0])
            name = list(EXPECTED_ARTIFACTS.values())[number - 1]
            return {"artifacts": [{"name": name, "expired": False, "size_in_bytes": 100}]}
        result = verify_pipeline_artifacts(report, fetch_by_run, "owner/repo", {})
        self.assertEqual(result["status"], "WORKFLOW_RUNS_PRESENT")
        self.assertIn("PRESENT", render_pipeline_dashboard(result))

    def test_missing_artifacts_block(self):
        result = verify_pipeline_artifacts(all_success(), lambda u, h: {"artifacts": []}, "owner/repo", {})
        self.assertEqual(result["status"], "WORKFLOW_VERIFICATION_INCOMPLETE")
        self.assertEqual(len(result["blockers"]), 5)
        self.assertIn("MISSING_OR_EXPIRED", render_pipeline_dashboard(result))

    def test_expired_artifact_blocks(self):
        result = verify_pipeline_artifacts(all_success(),
            lambda u, h: {"artifacts": [{"name": "project-et-council-history", "expired": True, "size_in_bytes": 100}]},
            "owner/repo", {})
        self.assertIn("archived_council_history", result["blockers"])

    def test_zero_byte_artifact_blocks(self):
        result = verify_pipeline_artifacts(all_success(),
            lambda u, h: {"artifacts": [{"name": "project-et-council-history", "expired": False, "size_in_bytes": 0}]},
            "owner/repo", {})
        self.assertIn("archived_council_history", result["blockers"])

    def test_fetch_error_blocks(self):
        def fail(url, headers):
            raise OSError("unavailable")
        result = verify_pipeline_artifacts(all_success(), fail, "owner/repo", {})
        self.assertEqual(result["workflows"]["combined_readiness"]["artifact_status"], "FETCH_ERROR")

    def test_unverified_run_skips_artifacts(self):
        report = all_success()
        report["workflows"]["combined_readiness"]["status"] = "NO_RUN_FOUND"
        result = verify_pipeline_artifacts(report, lambda u, h: {"artifacts": []}, "owner/repo", {})
        self.assertEqual(result["workflows"]["combined_readiness"]["artifact_status"], "NOT_CHECKED")

    def test_rejects_unsafe_report(self):
        report = all_success()
        report["orders_allowed"] = True
        with self.assertRaises(ValueError):
            verify_pipeline_artifacts(report, lambda u, h: {}, "owner/repo", {})

if __name__ == "__main__":
    unittest.main()
