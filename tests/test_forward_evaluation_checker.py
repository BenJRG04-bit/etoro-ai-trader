"""Regression tests for research-only forward evaluation reports."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "check_forward_evaluation.py"
TICKERS = ("AAPL", "MSFT", "NVDA", "SPY", "VTI")


def sample():
    return {
        "status": "PENDING",
        "evaluation": {
            "snapshot_date": "2026-10-30",
            "observations": {ticker: {"status": "PENDING_NEW_CLOSE"} for ticker in TICKERS},
            "research_only": True,
            "orders_allowed": False,
            "live_trading_approved": False,
        },
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
    }


def execute(data):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "report.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(CHECKER), str(path)],
            capture_output=True, text=True, check=False
        )


class ForwardEvaluationTests(unittest.TestCase):
    def test_pending_is_not_a_failure(self):
        result = execute(sample())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PENDING", result.stdout)

    def test_missing_safety_flag_fails_closed(self):
        data = sample()
        del data["orders_allowed"]
        self.assertNotEqual(execute(data).returncode, 0)

    def test_live_trading_approval_fails_closed(self):
        data = sample()
        data["evaluation"]["live_trading_approved"] = True
        self.assertNotEqual(execute(data).returncode, 0)

    def test_unknown_asset_fails_closed(self):
        data = sample()
        data["evaluation"]["observations"]["BTC"] = {"status": "PENDING_NEW_CLOSE"}
        self.assertNotEqual(execute(data).returncode, 0)

    def test_partial_evaluation_requires_review(self):
        data = sample()
        data["evaluation"]["observations"]["AAPL"]["status"] = "EVALUATED"
        result = execute(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PARTIAL", result.stdout)


if __name__ == "__main__":
    unittest.main()
