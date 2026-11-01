"""Read-only regression tests for historical strategy/benchmark evidence gate."""
import unittest
from copy import deepcopy

from paper_edge_audit import WATCHLIST, audit_historical_paper_edge


def sample_report(differences=None):
    differences = differences or {ticker: -1.00 for ticker in WATCHLIST}
    return {
        "mode": "HISTORICAL_PAPER_REPORT_NO_ORDERS",
        "starting_cash_gbp_per_asset": 100.0,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "assets": {
            ticker: {
                "status": "EXPLORATORY_ONLY",
                "report": {
                    "mode": "OFFLINE_PAPER_PERFORMANCE_NO_ORDERS",
                    "research_only": True,
                    "live_trading_approved": False,
                    "ticker": ticker,
                    "starting_cash": 100.0,
                    "strategy_end": 100.0 + delta,
                    "benchmark_end": 100.0,
                    "strategy_minus_benchmark_gbp": delta,
                },
            } for ticker, delta in differences.items()
        },
    }


class PaperEdgeAuditTests(unittest.TestCase):
    def test_underperformance_is_not_approval(self):
        result = audit_historical_paper_edge(sample_report())
        self.assertEqual(result["status"], "NO_CONSISTENT_HISTORICAL_EDGE")
        self.assertEqual(result["outperformed_count"], 0)
        self.assertFalse(result["orders_allowed"])
        self.assertFalse(result["demo_trading_approved"])
        self.assertFalse(result["live_trading_approved"])

    def test_five_positive_results_still_cannot_enable_trading(self):
        result = audit_historical_paper_edge(
            sample_report({ticker: 2.0 for ticker in WATCHLIST}))
        self.assertEqual(result["status"], "HISTORICAL_OUTPERFORMANCE_OBSERVED")
        self.assertEqual(result["outperformed_count"], 5)
        self.assertIn("TRADING_APPROVAL_NOT_GRANTED", result["blockers"])
        self.assertFalse(result["orders_allowed"])

    def test_partial_market_report_is_insufficient(self):
        data = sample_report()
        data["assets"]["NVDA"] = {"status": "UNAVAILABLE", "error_type": "URLError"}
        result = audit_historical_paper_edge(data)
        self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("NVDA_NOT_EVALUATED", result["blockers"])

    def test_missing_asset_blocks(self):
        data = sample_report()
        del data["assets"]["SPY"]
        self.assertEqual(audit_historical_paper_edge(data)["status"],
                         "INSUFFICIENT_EVIDENCE")

    def test_inconsistent_difference_blocks(self):
        data = sample_report()
        data["assets"]["SPY"]["report"]["strategy_minus_benchmark_gbp"] = 90
        result = audit_historical_paper_edge(data)
        self.assertIn("SPY_INCONSISTENT_COMPARISON", result["blockers"])

    def test_mismatched_ticker_blocks(self):
        data = sample_report()
        data["assets"]["SPY"]["report"]["ticker"] = "NVDA"
        self.assertIn("SPY_INVALID_REPORT",
                      audit_historical_paper_edge(data)["blockers"])

    def test_unsafe_source_is_refused(self):
        data = sample_report()
        data["orders_allowed"] = True
        result = audit_historical_paper_edge(data)
        self.assertIn("INVALID_OR_UNSAFE_SOURCE_REPORT", result["blockers"])

    def test_nonfinite_metrics_block(self):
        data = sample_report()
        data["assets"]["AAPL"]["report"]["strategy_end"] = float("nan")
        result = audit_historical_paper_edge(data)
        self.assertIn("AAPL_INVALID_METRICS", result["blockers"])

    def test_returns_always_research_only(self):
        for data in (None, {}, sample_report()):
            result = audit_historical_paper_edge(data)
            self.assertTrue(result["research_only"])
            self.assertFalse(result["orders_allowed"])
            self.assertFalse(result["demo_trading_approved"])
            self.assertFalse(result["live_trading_approved"])


if __name__ == "__main__":
    unittest.main()
