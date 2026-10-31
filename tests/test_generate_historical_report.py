"""Offline tests for historical report generation (no market network access)."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generate_historical_report


class GenerateHistoricalReportTests(unittest.TestCase):
    def test_writes_research_only_report(self):
        sample = {
            "mode": "HISTORICAL_RESEARCH_NO_ORDERS",
            "assets": {
                "SPY": {
                    "status": "EXPLORATORY_ONLY",
                    "evaluation": {"windows": [{
                        "baseline_return_fraction": 0.01,
                        "regime_return_fraction": 0.02,
                        "benchmark_return_fraction": 0.015,
                    }]},
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            original = os.getcwd()
            try:
                os.chdir(tmp)
                with patch.object(generate_historical_report,
                                  "run_historical_research", return_value=sample):
                    status = generate_historical_report.main()
                data = json.loads(Path("historical_research_report.json").read_text())
            finally:
                os.chdir(original)
        self.assertEqual(status, 0)
        self.assertFalse(data["live_trading_approved"])
        self.assertEqual(data["assets_unavailable"], [])
        self.assertEqual(data["assets"]["SPY"]["adaptive_wins_vs_hold"], 1)

    def test_failed_asset_returns_nonzero_but_saves_report(self):
        sample = {
            "mode": "HISTORICAL_RESEARCH_NO_ORDERS",
            "assets": {
                "NVDA": {"status": "DATA_OR_EVALUATION_UNAVAILABLE",
                         "error_type": "ValueError"},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            original = os.getcwd()
            try:
                os.chdir(tmp)
                with patch.object(generate_historical_report,
                                  "run_historical_research", return_value=sample):
                    status = generate_historical_report.main()
                data = json.loads(Path("historical_research_report.json").read_text())
            finally:
                os.chdir(original)
        self.assertEqual(status, 1)
        self.assertEqual(data["assets_unavailable"], ["NVDA"])
        self.assertFalse(data["live_trading_approved"])


if __name__ == "__main__":
    unittest.main()
