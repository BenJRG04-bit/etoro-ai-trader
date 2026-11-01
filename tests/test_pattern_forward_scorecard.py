"""Tests for conservative cumulative pattern-forward accounting."""
import copy
import json
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
import tempfile
import unittest

from historical_prices import WATCHLIST
from pattern_forward_scorecard import summarize_pattern_forward_outcomes
from run_pattern_forward_scorecard import run_scorecard

FEE = .001
SLIPPAGE = .001
COST = .05 * (FEE + SLIPPAGE)
SAFE = {"research_only": True, "orders_allowed": False,
        "demo_trading_approved": False, "live_trading_approved": False}


def report(index, *, candidate_symbol="AAPL"):
    d = date(2026, 1, 1) + timedelta(days=index)
    entry = d + timedelta(days=2)
    exit_day = d + timedelta(days=3)
    rows = {}
    for ticker in WATCHLIST:
        active = ticker == candidate_symbol
        raw_return = 0.02 if ticker in ("AAPL", "SPY") else -0.02
        held = 100 * (1 - COST) ** 2 * (1 + .05 * raw_return)
        strategy = held if active else 100.0
        held, strategy = round(held, 6), round(strategy, 6)
        rows[ticker] = {
            "status": "OBSERVED",
            "archived_signal": "RESEARCH_CANDIDATE" if active else "NO_CANDIDATE",
            "entry_close_date": entry.isoformat(),
            "exit_close_date": exit_day.isoformat(),
            "raw_price_return": raw_return,
            "hypothetical_signal_equity": strategy,
            "hypothetical_matched_hold_equity": held,
            "signal_minus_matched_hold": round(strategy - held, 6),
            "signal_beat_matched_hold": strategy > held,
        }
    return {
        **SAFE,
        "status": "OBSERVED", "signal_close_date": d.isoformat(),
        "archived_at_utc": datetime.combine(
            d + timedelta(days=1), datetime.min.time(),
            tzinfo=timezone.utc).replace(hour=23).isoformat(),
        "strategy_version": "pattern-confluence-v1",
        "observations": rows, "observed_count": 5,
        "pending_count": 0, "research_candidates_observed": 1,
        "comparison_fee_rate": FEE, "comparison_slippage_rate": SLIPPAGE,
    }


class ForwardScorecardTests(unittest.TestCase):
    def test_empty_history_never_approves_trade(self):
        result = summarize_pattern_forward_outcomes([])
        self.assertEqual(result["status"], "MORE_FORWARD_EVIDENCE_REQUIRED")
        self.assertEqual(result["unique_signal_dates"], 0)
        self.assertFalse(result["orders_allowed"])
        self.assertFalse(result["demo_trading_approved"])

    def test_counts_missed_gains_and_avoided_losses(self):
        result = summarize_pattern_forward_outcomes([report(i) for i in range(3)])
        self.assertEqual(result["unique_signal_dates"], 3)
        self.assertEqual(result["observed_asset_days"], 15)
        self.assertEqual(result["candidate_asset_days"], 3)
        self.assertEqual(result["candidate_net_positive_days"], 3)
        self.assertGreater(result["noncandidate_avoided_net_loss"], 0)
        self.assertGreater(result["noncandidate_missed_net_gain"], 0)
        self.assertEqual(result["per_asset"]["AAPL"]["candidate_days"], 3)
        self.assertFalse(result["live_trading_approved"])

    def test_twenty_dates_still_no_execution(self):
        result = summarize_pattern_forward_outcomes([report(i) for i in range(20)])
        self.assertEqual(result["status"], "SAMPLE_AVAILABLE_FOR_MANUAL_REVIEW_ONLY")
        self.assertEqual(result["unique_signal_dates"], 20)
        self.assertEqual(result["candidate_asset_days"], 20)
        self.assertIn("NO_AUTOMATED_TRADING_APPROVAL", result["blockers"])
        self.assertFalse(result["orders_allowed"])
        self.assertFalse(result["demo_trading_approved"])

    def test_five_correlated_assets_are_not_five_dates(self):
        result = summarize_pattern_forward_outcomes([report(i) for i in range(4)])
        self.assertEqual(result["unique_signal_dates"], 4)
        self.assertEqual(result["observed_asset_days"], 20)
        self.assertIn("TOO_FEW_UNIQUE_FORWARD_DATES", result["blockers"])

    def test_pending_does_not_count_as_observed(self):
        result = summarize_pattern_forward_outcomes(
            [report(0), {**SAFE, "status": "PENDING"}])
        self.assertEqual(result["unique_signal_dates"], 1)
        self.assertEqual(result["pending_archive_reports"], 1)

    def test_identical_duplicates_not_counted_twice(self):
        row = report(0)
        result = summarize_pattern_forward_outcomes([row, copy.deepcopy(row)])
        self.assertEqual(result["unique_signal_dates"], 1)
        self.assertEqual(result["identical_duplicate_reports_ignored"], 1)

    def test_conflicting_duplicates_rejected(self):
        original, duplicate = report(0), report(0)
        row = duplicate["observations"]["AAPL"]
        row["archived_signal"] = "NO_CANDIDATE"
        row["hypothetical_signal_equity"] = 100.0
        row["signal_minus_matched_hold"] = round(
            100 - row["hypothetical_matched_hold_equity"], 6)
        row["signal_beat_matched_hold"] = (
            100 > row["hypothetical_matched_hold_equity"])
        duplicate["research_candidates_observed"] = 0
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            summarize_pattern_forward_outcomes([original, duplicate])

    def test_tampered_returns_and_future_entries_rejected(self):
        bad = report(0)
        bad["observations"]["AAPL"]["hypothetical_signal_equity"] = 200
        with self.assertRaises(ValueError):
            summarize_pattern_forward_outcomes([bad])
        bad = report(0)
        bad["archived_at_utc"] = "2026-01-09T23:00:00+00:00"
        with self.assertRaises(ValueError):
            summarize_pattern_forward_outcomes([bad])

    def test_unsafe_or_unavailable_not_silently_skipped(self):
        unsafe = report(0)
        unsafe["orders_allowed"] = True
        with self.assertRaises(ValueError):
            summarize_pattern_forward_outcomes([unsafe])
        with self.assertRaises(ValueError):
            summarize_pattern_forward_outcomes([{**SAFE, "status": "UNAVAILABLE"}])

    def test_requires_multiple_candidates_in_sufficient_dates(self):
        r = [report(i, candidate_symbol="NOT_IN_WATCHLIST") for i in range(20)]
        for item in r:
            item["research_candidates_observed"] = 0
        result = summarize_pattern_forward_outcomes(r)
        self.assertEqual(result["unique_signal_dates"], 20)
        self.assertEqual(result["candidate_asset_days"], 0)
        self.assertIn("TOO_FEW_PRECOMMITTED_RESEARCH_CANDIDATES", result["blockers"])

    def test_rolling_runner_flags_missing_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / "first_run"
            child.mkdir()
            (child / "pattern_forward_evaluation.json").write_text(
                json.dumps(report(0)), encoding="utf-8")
            (root / "manifest.json").write_text(
                json.dumps({"downloaded": 1, "unavailable": [123]}), encoding="utf-8")
            result = run_scorecard(root)
            self.assertEqual(result["status"], "INCOMPLETE_ARCHIVE_SET")
            self.assertIn("MISSING_ARCHIVED_RUNS", result["blockers"])
            self.assertFalse(result["orders_allowed"])

    def test_invalid_artifact_runner_returns_safe_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / "run"
            child.mkdir()
            (child / "pattern_forward_evaluation.json").write_text(
                "{bad json", encoding="utf-8")
            result = run_scorecard(root)
            self.assertEqual(result["status"], "INVALID_INPUTS")
            self.assertFalse(result["live_trading_approved"])


if __name__ == "__main__":
    unittest.main()
