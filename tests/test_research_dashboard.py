import json
import tempfile
import unittest
from pathlib import Path
from research_dashboard import render_dashboard, build_dashboard, REPORT_FILES

def item(status="EXPLORATORY_ONLY", **kwargs):
    return {"status": status, **kwargs}

class DashboardTests(unittest.TestCase):
    def test_renders_known_paper_fields(self):
        reports = {
            "paper": {"assets": {"SPY": item(report={"strategy_end": 99.5, "benchmark_end": 101.25})}},
            "quality": {"assets": {"SPY": item(sample_adequate=False)}},
            "severity": {"assets": {"SPY": item(severity={"horizons": {"20": {"veto": {"worst_return_fraction": -0.12}}}})}},
            "holdout": {"assets": {"SPY": item(audit={"segments": {"later_holdout": {"horizons": {"20": {"veto": {"observations": 4}}}}}})}},
        }
        result = render_dashboard(reports, generated_at="test")
        self.assertIn("£99.50", result)
        self.assertIn("£101.25", result)
        self.assertIn("-12.00%", result)
        self.assertIn("INSUFFICIENT", result)
        self.assertIn("4</td>", result)

    def test_escapes_untrusted_ticker(self):
        result = render_dashboard({"paper": {"assets": {"<script>alert(1)</script>": item()}}}, generated_at="<unsafe>")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)
        self.assertIn("&lt;unsafe&gt;", result)

    def test_empty_reports_still_safe(self):
        result = render_dashboard({})
        self.assertIn("NO ORDERS OR LIVE TRADING", result)
        self.assertIn("<table>", result)

    def test_rejects_unsafe_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / REPORT_FILES["paper"]
            path.write_text(json.dumps({"research_only": False, "orders_allowed": True, "assets": {}}))
            with self.assertRaises(ValueError):
                build_dashboard(folder)

    def test_build_with_missing_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            out = build_dashboard(folder)
            self.assertTrue(Path(out).exists())
            self.assertIn("Missing results", Path(out).read_text())

    def test_build_with_safe_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / REPORT_FILES["paper"]
            path.write_text(json.dumps({"research_only": True, "orders_allowed": False, "assets": {"AAPL": item(report={"strategy_end": 100.2})}}))
            out = build_dashboard(folder)
            self.assertIn("AAPL", Path(out).read_text())
            self.assertIn("£100.20", Path(out).read_text())

if __name__ == "__main__":
    unittest.main()
