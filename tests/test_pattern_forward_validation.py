"""Chronology, leakage and safety tests for archived pattern forward signals."""
import copy
from datetime import date, datetime, timedelta, timezone
import unittest

from run_pattern_forward_snapshot import (
    create_pattern_forward_snapshot, run_pattern_forward_snapshot,
)
from run_pattern_forward_evaluation import (
    evaluate_pattern_forward_snapshot, run_pattern_forward_evaluation,
    validate_pattern_forward_snapshot,
)
from pattern_archive_run_selection import select_prior_pattern_run
from historical_prices import WATCHLIST


SIGNAL_DAY = date(2026, 10, 30)
CREATED = datetime(2026, 11, 1, 18, 30, tzinfo=timezone.utc)
SCORED = datetime(2026, 11, 4, 10, tzinfo=timezone.utc)


def history(ticker):
    start = SIGNAL_DAY - timedelta(days=259)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(260)]
    closes = [100.0 + 0.13 * i + (0.4 if i % 2 else -0.4) for i in range(260)]
    return {"ticker": ticker, "dates": dates, "closes": closes,
            "price_type": "unadjusted_daily_close"}


def all_histories():
    return {symbol: history(symbol) for symbol in WATCHLIST}


def later(histories, *, one=False):
    rows = copy.deepcopy(histories)
    for row in rows.values():
        row["dates"].append("2026-11-02")
        row["closes"].append(row["closes"][-1] * 1.01)
        if not one:
            row["dates"].append("2026-11-03")
            row["closes"].append(row["closes"][-1] * 0.99)
    return rows


def frozen(histories=None):
    inputs = all_histories() if histories is None else histories
    return {
        "status": "PATTERN_SNAPSHOT_RESEARCH_ONLY",
        "research_only": True, "orders_allowed": False,
        "demo_trading_approved": False, "live_trading_approved": False,
        "snapshot": create_pattern_forward_snapshot(inputs, now_utc=CREATED),
    }


class ForwardPatternTests(unittest.TestCase):
    def test_freezes_all_five_without_future(self):
        doc = frozen()
        snap = validate_pattern_forward_snapshot(doc, evaluated_at=SCORED)
        self.assertEqual(snap["signal_close_date"], "2026-10-30")
        self.assertEqual(set(snap["assets"]), set(WATCHLIST))
        self.assertEqual(snap["strategy_version"], "pattern-confluence-v1")
        self.assertFalse(snap["orders_allowed"])

    def test_first_or_zero_new_closes_are_pending(self):
        for rows in (all_histories(), later(all_histories(), one=True)):
            result = evaluate_pattern_forward_snapshot(
                frozen(), rows, evaluated_at=SCORED)
            self.assertEqual(result["status"], "PENDING")
            self.assertEqual(result["observed_count"], 0)
            self.assertEqual(result["pending_count"], 5)
            self.assertFalse(result["orders_allowed"])

    def test_two_new_closes_have_next_day_entry_and_costs(self):
        doc = frozen()
        result = evaluate_pattern_forward_snapshot(
            doc, later(all_histories()), evaluated_at=SCORED)
        self.assertEqual(result["status"], "OBSERVED")
        self.assertEqual(result["observed_count"], 5)
        self.assertFalse(result["live_trading_approved"])
        for row in result["observations"].values():
            self.assertEqual(row["entry_close_date"], "2026-11-02")
            self.assertEqual(row["exit_close_date"], "2026-11-03")
            self.assertLess(row["hypothetical_matched_hold_equity"], 100)
            self.assertTrue(type(row["raw_price_return"]) is float)

    def test_precommitted_non_candidate_stays_cash(self):
        doc = frozen()
        for row in doc["snapshot"]["assets"].values():
            row["signal"] = "NO_CANDIDATE"
            row["pattern_score"] = 0
            row["risk_vetoes"] = []
        result = evaluate_pattern_forward_snapshot(
            doc, later(all_histories()), evaluated_at=SCORED)
        self.assertEqual(result["research_candidates_observed"], 0)
        for row in result["observations"].values():
            self.assertEqual(row["hypothetical_signal_equity"], 100.0)

    def test_delayed_archive_cannot_claim_next_close_entry(self):
        doc = frozen()
        doc["snapshot"]["generated_at_utc"] = "2026-11-02T23:15:00+00:00"
        with self.assertRaisesRegex(ValueError, "after the simulated entry"):
            evaluate_pattern_forward_snapshot(
                doc, later(all_histories()), evaluated_at=SCORED)

    def test_revised_historical_close_is_rejected(self):
        rows = later(all_histories())
        rows["AAPL"]["closes"][-3] *= 1.02
        with self.assertRaisesRegex(ValueError, "revised"):
            evaluate_pattern_forward_snapshot(frozen(), rows, evaluated_at=SCORED)

    def test_strict_risk_veto_stays_in_archive(self):
        doc = frozen()
        row = doc["snapshot"]["assets"]["SPY"]
        row["signal"] = "RESEARCH_CANDIDATE"
        row["risk_vetoes"] = ["HIGH_DAILY_VOLATILITY"]
        with self.assertRaisesRegex(ValueError, "contradicts"):
            validate_pattern_forward_snapshot(doc, evaluated_at=SCORED)

    def test_wont_score_unfinished_exit_date(self):
        with self.assertRaisesRegex(ValueError, "might be incomplete"):
            evaluate_pattern_forward_snapshot(
                frozen(), later(all_histories()),
                evaluated_at=datetime(2026, 11, 3, 9, tzinfo=timezone.utc))

    def test_today_unfinalized_close_fails_snapshot(self):
        rows = all_histories()
        with self.assertRaisesRegex(ValueError, "not safely final"):
            create_pattern_forward_snapshot(rows, now_utc=datetime(
                2026, 10, 30, 19, tzinfo=timezone.utc))

    def test_missing_asset_or_date_alignment_fails(self):
        rows = all_histories()
        del rows["VTI"]
        with self.assertRaises(ValueError):
            create_pattern_forward_snapshot(rows, now_utc=CREATED)
        rows = all_histories()
        rows["VTI"]["dates"][-1] = "2026-10-31"
        with self.assertRaises(ValueError):
            create_pattern_forward_snapshot(rows, now_utc=CREATED)

    def test_no_demo_or_real_orders_ever(self):
        doc = frozen()
        result = evaluate_pattern_forward_snapshot(
            doc, later(all_histories()), evaluated_at=SCORED)
        for obj in (doc, doc["snapshot"], result):
            self.assertTrue(obj["research_only"])
            self.assertFalse(obj["orders_allowed"])
            self.assertFalse(obj["demo_trading_approved"])
            self.assertFalse(obj["live_trading_approved"])

    def test_source_or_schema_tampering_is_rejected(self):
        for change in (("strategy_version", "v2"), ("schema_version", 2),
                       ("source", "broker-live")):
            doc = frozen()
            doc["snapshot"][change[0]] = change[1]
            with self.assertRaises(ValueError):
                validate_pattern_forward_snapshot(doc, evaluated_at=SCORED)

    def test_fetcher_error_does_not_fabricate_snapshot(self):
        def missing(ticker, period="2y"):
            raise OSError("No data")
        result = run_pattern_forward_snapshot(fetcher=missing, now_utc=CREATED)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertFalse(result["orders_allowed"])
        evaluated = run_pattern_forward_evaluation(
            None, fetcher=missing, evaluated_at=SCORED)
        self.assertEqual(evaluated["status"], "UNAVAILABLE")

    def test_no_future_price_allowed_when_archiving(self):
        observed = []
        import run_pattern_forward_snapshot as runner
        original = runner.analyze_price_patterns

        def record(closes):
            observed.append(len(closes))
            return original(closes)
        from unittest.mock import patch
        with patch("run_pattern_forward_snapshot.analyze_price_patterns", side_effect=record):
            create_pattern_forward_snapshot(all_histories(), now_utc=CREATED)
        self.assertEqual(observed, [260] * 5)


class PatternRunSelectionTests(unittest.TestCase):
    def row(self, id, stamp, **overrides):
        return {"id": id, "updated_at": stamp,
                "head_branch": "main", "status": "completed",
                "conclusion": "success", **overrides}

    def test_select_mature_run_not_newest(self):
        records = [self.row(21, "2026-11-04T01:00:00Z"),
                   self.row(20, "2026-11-01T23:00:00Z"),
                   self.row(19, "2026-10-30T23:00:00Z")]
        self.assertEqual(select_prior_pattern_run(
            records, evaluated_at="2026-11-04T10:00:00Z"), 20)

    def test_bad_branch_failed_and_future_runs_ignored(self):
        records = [self.row(10, "2026-10-27T23:00:00Z", head_branch="other"),
                   self.row(11, "2026-10-27T23:00:00Z", conclusion="failure"),
                   self.row(12, "2026-11-04T11:00:00Z")]
        self.assertIsNone(select_prior_pattern_run(
            records, evaluated_at="2026-11-04T10:00:00Z"))

    def test_requires_timezone_and_reasonable_age(self):
        with self.assertRaises(ValueError):
            select_prior_pattern_run([], evaluated_at="2026-11-04T10:00:00")
        with self.assertRaises(ValueError):
            select_prior_pattern_run([], evaluated_at="2026-11-04T10:00:00Z",
                                     minimum_age_hours=0)


if __name__ == "__main__":
    unittest.main()
