import json
import tempfile
import unittest
from pathlib import Path
from workflow_run_diagnostics import summarize_workflow_runs, WORKFLOWS
from workflow_diagnostics_dashboard import render_pipeline_dashboard, build_pipeline_dashboard

class PipelineDashboardTests(unittest.TestCase):
    def setUp(self):
        self.report = summarize_workflow_runs([])

    def test_no_runs_visible(self):
        page = render_pipeline_dashboard(self.report)
        self.assertIn("NO_RUN_FOUND", page)
        self.assertIn("5 of 5", page)

    def test_read_only_warning(self):
        self.assertIn("NO LIVE TRADING", render_pipeline_dashboard(self.report))

    def test_rejects_unsafe(self):
        self.report["orders_allowed"] = True
        with self.assertRaises(ValueError):
            render_pipeline_dashboard(self.report)

    def test_rejects_missing_workflow(self):
        self.report["workflows"].pop(next(iter(WORKFLOWS.values())))
        with self.assertRaises(ValueError):
            render_pipeline_dashboard(self.report)

    def test_rejects_false_success(self):
        self.report["status"] = "WORKFLOW_RUNS_PRESENT"
        with self.assertRaises(ValueError):
            render_pipeline_dashboard(self.report)

    def test_rejects_inconsistent_blockers(self):
        self.report["blockers"] = []
        with self.assertRaises(ValueError):
            render_pipeline_dashboard(self.report)

    def test_rejects_unknown_status(self):
        key = next(iter(WORKFLOWS.values()))
        self.report["workflows"][key]["status"] = "TRADE"
        with self.assertRaises(ValueError):
            render_pipeline_dashboard(self.report)

    def test_escapes_metadata(self):
        key = next(iter(WORKFLOWS.values()))
        self.report["workflows"][key]["conclusion"] = "<script>alert(1)</script>"
        page = render_pipeline_dashboard(self.report)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_writes_html(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "workflow_diagnostics_report.json").write_text(json.dumps(self.report))
            self.assertTrue(Path(build_pipeline_dashboard(folder)).is_file())

if __name__ == "__main__":
    unittest.main()
