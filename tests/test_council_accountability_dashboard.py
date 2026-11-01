import json
import tempfile
import unittest
from pathlib import Path
from council_accountability_dashboard import render_council_dashboard, build_council_dashboard
from six_brains import NAMES

class CouncilDashboardTests(unittest.TestCase):
    def setUp(self):
        self.report = {"status": "RESEARCH_ACCOUNTABILITY_ONLY",
                       "research_only": True, "orders_allowed": False,
                       "live_trading_approved": False,
                       "assets": {"SPY": {"status": "OBSERVED_RESEARCH",
                           "as_of": "2026-10-30",
                           "explanation": {"status": "RESEARCH_EXPLANATION",
                               "orders_allowed": False, "market_regime": "UPTREND",
                               "original_decision": "POSITIVE_RESEARCH",
                               "confirmed_decision": "WAIT_FOR_CONFIRMATION",
                               "risk_veto": False,
                               "agreement": {"positive": 3, "negative": 2, "neutral": 1},
                               "perspectives": {name: {"score": 0.5, "stance": "POSITIVE"} for name in NAMES},
                               "reasons": ["Previous close did not confirm"]}}}}

    def test_summary_and_breakdown(self):
        page = render_council_dashboard(self.report)
        self.assertIn("SPY", page)
        self.assertIn("WAIT_FOR_CONFIRMATION", page)
        self.assertIn("optimist", page)
        self.assertIn("NO ORDERS OR LIVE TRADING", page)

    def test_escapes_untrusted_ticker(self):
        self.report["assets"]["<script>alert(1)</script>"] = self.report["assets"].pop("SPY")
        page = render_council_dashboard(self.report)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_rejects_orders_enabled(self):
        self.report["orders_allowed"] = True
        with self.assertRaises(ValueError):
            render_council_dashboard(self.report)

    def test_rejects_missing_perspective(self):
        self.report["assets"]["SPY"]["explanation"]["perspectives"].pop("optimist")
        with self.assertRaises(ValueError):
            render_council_dashboard(self.report)

    def test_unavailable_explicit(self):
        self.report["assets"]["SPY"] = {"status": "UNAVAILABLE"}
        self.assertIn("No verified assessment", render_council_dashboard(self.report))

    def test_writes_static_html(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "council_accountability_report.json").write_text(json.dumps(self.report))
            output = build_council_dashboard(d)
            self.assertTrue(Path(output).exists())
            self.assertNotIn("<script", Path(output).read_text())

if __name__ == "__main__":
    unittest.main()
