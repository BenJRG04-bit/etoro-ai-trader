"""Regression tests ensuring GitHub batches do not skip archived market days."""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import copy
import json
import tempfile
import unittest

from historical_prices import WATCHLIST
from pattern_archive_run_selection import select_mature_pattern_runs
from run_pattern_forward_snapshot import create_pattern_forward_snapshot
from run_pattern_forward_batch import run_pattern_forward_batch

NOW = datetime(2026, 11, 4, 11, tzinfo=timezone.utc)
FREEZE_FRI = datetime(2026, 11, 1, 18, 30, tzinfo=timezone.utc)
FREEZE_THU = datetime(2026, 10, 29, 23, 15, tzinfo=timezone.utc)
SIGNAL_DAY = date(2026, 10, 30)


def market_rows():
    start = SIGNAL_DAY - timedelta(days=259)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(260)]
    rows = {}
    for ticker in WATCHLIST:
        prices = [100 + i * .12 + (.4 if i % 2 else -.4) for i in range(260)]
        rows[ticker] = {
            "ticker": ticker, "dates": dates[:], "closes": prices,
            "price_type": "unadjusted_daily_close",
        }
    return rows


def archived(rows, generated):
    return {
        "status": "PATTERN_SNAPSHOT_RESEARCH_ONLY",
        "research_only": True, "orders_allowed": False,
        "demo_trading_approved": False,
        "live_trading_approved": False,
        "snapshot": create_pattern_forward_snapshot(rows, now_utc=generated),
    }


def extended(rows):
    copied = copy.deepcopy(rows)
    for row in copied.values():
        row["dates"].extend(["2026-11-02", "2026-11-03"])
        row["closes"].extend([row["closes"][-1] * 1.01,
                              row["closes"][-1] * 0.99])
    return copied


def write_archive(root, run_id, payload):
    path = root / str(run_id)
    path.mkdir()
    (path / "pattern_forward_snapshot.json").write_text(
        json.dumps(payload), encoding="utf-8")


class SelectPatternBatchTests(unittest.TestCase):
    def run(self, rid, stamp, **changes):
        return {
            "id": rid, "created_at": stamp, "updated_at": stamp,
            "head_branch": "main", "status": "completed",
            "conclusion": "success", **changes,
        }

    def test_weekend_maturity_includes_thursday_and_friday(self):
        runs = [
            self.run(21, "2026-11-09T23:15:00Z"),  # too new
            self.run(20, "2026-11-06T23:15:00Z"),  # Fri
            self.run(19, "2026-11-05T23:15:00Z"),  # Thu
            self.run(18, "2026-11-04T23:15:00Z"),  # Wed
        ]
        selected = select_mature_pattern_runs(
            runs, evaluated_at="2026-11-10T03:15:00Z")
        self.assertEqual(selected, [20, 19, 18])
        self.assertIn(19, selected)

    def test_not_yet_mature_and_legacy_skipped(self):
        runs = [
            self.run(1, "2026-10-28T23:00:00Z"),
            self.run(2, "2026-11-08T23:00:00Z"),
            self.run(3, "2026-11-04T23:00:00Z", head_branch="topic"),
            self.run(4, "2026-11-04T23:00:00Z", conclusion="failure"),
        ]
        self.assertEqual(select_mature_pattern_runs(
            runs, evaluated_at="2026-11-10T00:00:00Z"), [])

    def test_batch_size_and_timezone_checked(self):
        with self.assertRaises(ValueError):
            select_mature_pattern_runs([], evaluated_at="2026-11-10T03:00:00Z",
                                      max_runs=100)
        with self.assertRaises(ValueError):
            select_mature_pattern_runs([], evaluated_at="2026-11-10T03:00:00")

    def test_returns_newest_mature_limited_batch(self):
        runs = [self.run(i, f"2026-11-{i:02}T23:00:00Z")
                for i in (2, 3, 4, 5, 6)]
        self.assertEqual(
            select_mature_pattern_runs(runs, evaluated_at="2026-11-09T03:00:00Z",
                                       max_runs=3), [6, 5, 4])


class PatternBatchRunnerTests(unittest.TestCase):
    def test_evaluates_two_different_archived_dates_with_one_market_download(self):
        historical = market_rows()
        friday = archived(historical, FREEZE_FRI)
        prior = copy.deepcopy(historical)
        for row in prior.values():
            row["dates"] = row["dates"][:-1]
            row["closes"] = row["closes"][:-1]
        thursday = archived(prior, FREEZE_THU)
        latest = extended(historical)

        calls = []
        def fetch(ticker, period="2y"):
            calls.append(ticker)
            return latest[ticker]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources, outputs = root / "snapshots", root / "evaluations"
            sources.mkdir()
            write_archive(sources, 111, thursday)
            write_archive(sources, 112, friday)
            result = run_pattern_forward_batch(
                sources, outputs, fetcher=fetch, evaluated_at=NOW)
            self.assertEqual(result["status"], "BATCH_COMPLETE")
            self.assertEqual(result["archives"], 2)
            self.assertEqual(result["observed"], 2)
            self.assertEqual(result["market_downloads"], 5)
            self.assertEqual(sorted(calls), sorted(WATCHLIST))
            th = json.loads((outputs / "111/pattern_forward_evaluation.json").read_text())
            fr = json.loads((outputs / "112/pattern_forward_evaluation.json").read_text())
            self.assertEqual(th["signal_close_date"], "2026-10-29")
            self.assertEqual(fr["signal_close_date"], "2026-10-30")
            self.assertEqual(th["status"], "OBSERVED")
            self.assertEqual(fr["status"], "OBSERVED")
            self.assertFalse(th["orders_allowed"])
            self.assertFalse(fr["live_trading_approved"])

    def test_one_future_close_is_not_misreported_as_outcome(self):
        original = market_rows()
        latest = copy.deepcopy(original)
        for row in latest.values():
            row["dates"].append("2026-11-02")
            row["closes"].append(row["closes"][-1] * 1.01)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources, outputs = root / "in", root / "out"
            sources.mkdir()
            write_archive(sources, 333, archived(original, FREEZE_FRI))
            result = run_pattern_forward_batch(
                sources, outputs, fetcher=lambda ticker, period="2y": latest[ticker],
                evaluated_at=NOW)
            self.assertEqual(result["status"], "BATCH_COMPLETE")
            self.assertEqual(result["pending"], 1)
            self.assertEqual(result["observed"], 0)

    def test_missing_archived_snapshot_fails_closed(self):
        original = market_rows()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources, outputs = root / "in", root / "out"
            sources.mkdir()
            write_archive(sources, 111, archived(original, FREEZE_FRI))
            (sources / "112").mkdir()
            result = run_pattern_forward_batch(
                sources, outputs,
                fetcher=lambda ticker, period="2y": extended(original)[ticker],
                evaluated_at=NOW)
            self.assertEqual(result["status"], "BATCH_INCOMPLETE")
            self.assertEqual(result["unavailable"], 1)
            missing = json.loads((outputs / "112/pattern_forward_evaluation.json").read_text())
            self.assertEqual(missing["status"], "UNAVAILABLE")
            self.assertFalse(missing["orders_allowed"])

    def test_network_outage_does_not_create_returns(self):
        original = market_rows()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources, outputs = root / "in", root / "out"
            sources.mkdir()
            write_archive(sources, 111, archived(original, FREEZE_FRI))
            def no_market(ticker, period="2y"):
                raise OSError("provider inaccessible")
            result = run_pattern_forward_batch(
                sources, outputs, fetcher=no_market, evaluated_at=NOW)
            self.assertEqual(result["status"], "BATCH_INCOMPLETE")
            self.assertEqual(result["market_downloads"], 0)
            missing = json.loads((outputs / "111/pattern_forward_evaluation.json").read_text())
            self.assertEqual(missing["status"], "UNAVAILABLE")
            self.assertFalse(missing["live_trading_approved"])

    def test_empty_archives_report_pending_without_prices(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources, outputs = root / "in", root / "out"
            sources.mkdir()
            def never_fetch(*args, **kwargs):
                self.fail("Must not fetch when no archives exist")
            result = run_pattern_forward_batch(
                sources, outputs, fetcher=never_fetch, evaluated_at=NOW)
            self.assertEqual(result["status"], "PENDING")
            self.assertEqual(result["market_downloads"], 0)
            pending = json.loads((outputs / "status/pattern_forward_evaluation.json").read_text())
            self.assertEqual(pending["status"], "PENDING")
            self.assertFalse(pending["orders_allowed"])


if __name__ == "__main__":
    unittest.main()
