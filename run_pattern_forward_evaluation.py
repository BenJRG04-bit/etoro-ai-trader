"""Assess PRE-ARCHIVED Project E.T. pattern calls against later public closes.

Conservative timeline: signal frozen after day S closes; observe day E close
(strictly after archive calendar date); score E->X close return on a later day X.
This avoids using a same-close signal as a free fill. Still a *hypothetical*
close-to-close outcome, not real broker prices or executed trade fills.
"""
from datetime import date, datetime, timezone
import json
from math import isfinite
import sys

from historical_prices import WATCHLIST, fetch_daily_closes
from run_pattern_forward_snapshot import VERSION, SCHEMA_VERSION

SIGNALS = {"RESEARCH_CANDIDATE", "NO_CANDIDATE", "RISK_BLOCKED"}
SAFE = {"research_only": True, "orders_allowed": False,
        "demo_trading_approved": False, "live_trading_approved": False}


def _finite_positive(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def _date(value):
    if not isinstance(value, str):
        raise ValueError("Date missing")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Noncanonical date")
    return parsed


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp must be timezone-aware")
    parsed = parsed.astimezone(timezone.utc)
    if not value.endswith(("+00:00", "Z")):
        raise ValueError("UTC timestamp required")
    return parsed


def validate_pattern_forward_snapshot(document, *, evaluated_at=None):
    if (not isinstance(document, dict)
        or document.get("status") != "PATTERN_SNAPSHOT_RESEARCH_ONLY"):
        raise ValueError("Not a frozen pattern research snapshot")
    for source in (document, document.get("snapshot")):
        if not isinstance(source, dict):
            raise ValueError("Incomplete research envelope")
        for key, expected in SAFE.items():
            if source.get(key) is not expected:
                raise ValueError("Unsafe archived snapshot")
    snap = document["snapshot"]
    if (type(snap.get("schema_version")) is not int
        or snap["schema_version"] != SCHEMA_VERSION
        or snap.get("strategy_version") != VERSION
        or snap.get("source") != "public_unadjusted_daily_close"):
        raise ValueError("Unrecognized or revised strategy/data schema")
    as_of = _date(snap.get("signal_close_date"))
    created = _timestamp(snap.get("generated_at_utc"))
    now = datetime.now(timezone.utc) if evaluated_at is None else evaluated_at
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Evaluation must have an aware timestamp")
    now = now.astimezone(timezone.utc)
    if created > now or not 0 <= (created.date() - as_of).days <= 4:
        raise ValueError("Invalid chronology of archived signal")
    if created.date() == as_of and created.hour < 22:
        raise ValueError("Snapshot captured before same-day close finality")
    rows = snap.get("assets")
    if not isinstance(rows, dict) or set(rows) != set(WATCHLIST):
        raise ValueError("Archived watchlist differs")
    for ticker, entry in rows.items():
        if not isinstance(entry, dict) or not _finite_positive(entry.get("signal_close")):
            raise ValueError("Invalid archived close: " + ticker)
        if entry.get("signal") not in SIGNALS:
            raise ValueError("Unrecognized archived signal: " + ticker)
        score = entry.get("pattern_score")
        if type(score) is not int or not 0 <= score <= 8:
            raise ValueError("Invalid fixed pattern score")
        for key in ("pattern_labels", "risk_vetoes"):
            values = entry.get(key)
            if (not isinstance(values, list) or
                any(not isinstance(v, str) or not v for v in values) or
                len(values) != len(set(values))):
                raise ValueError("Invalid archived pattern descriptors")
        if entry["signal"] == "RESEARCH_CANDIDATE" and (score < 4 or entry["risk_vetoes"]):
            raise ValueError("Candidate contradicts archived risk policy")
    return snap


def _hypothetical_end(value, asset_return, *, fee_rate, slippage_rate):
    """5%-allocation, entry and exit charged, no leverage or compounding."""
    fraction = 0.05
    turn_cost = fraction * (fee_rate + slippage_rate)
    return value * (1 - turn_cost) * (1 + fraction * asset_return) * (1 - turn_cost)


def evaluate_pattern_forward_snapshot(document, histories, *, evaluated_at=None,
                                      fee_rate=0.001, slippage_rate=0.001):
    snap = validate_pattern_forward_snapshot(document, evaluated_at=evaluated_at)
    if (type(fee_rate) not in (float, int) or not isfinite(fee_rate) or not 0 <= fee_rate < 0.1
        or type(slippage_rate) not in (float, int) or not isfinite(slippage_rate)
        or not 0 <= slippage_rate < 0.05):
        raise ValueError("Invalid friction assumptions")
    if not isinstance(histories, dict) or set(histories) != set(WATCHLIST):
        raise ValueError("Incomplete or mismatched evaluation universe")
    observed_at = datetime.now(timezone.utc) if evaluated_at is None else evaluated_at
    observed_at = observed_at.astimezone(timezone.utc)
    created_day = _timestamp(snap["generated_at_utc"]).date()
    signal_day = _date(snap["signal_close_date"])

    observed, pending = {}, []
    dates_equal = None
    for ticker in WATCHLIST:
        history = histories[ticker]
        if (not isinstance(history, dict) or history.get("ticker") != ticker
            or history.get("price_type") != "unadjusted_daily_close"):
            raise ValueError("Mismatched or adjusted market data")
        dates, prices = history.get("dates"), history.get("closes")
        if (not isinstance(dates, list) or not isinstance(prices, (tuple, list))
            or len(dates) != len(prices) or len(dates) < 120
            or any(not _finite_positive(p) for p in prices)):
            raise ValueError("Invalid evaluation history")
        parsed = [_date(d) for d in dates]
        if parsed != sorted(set(parsed)):
            raise ValueError("Unordered or repeated close dates")
        if dates_equal is None:
            dates_equal = dates
        elif dates_equal != dates:
            raise ValueError("Evaluation dates disagree across assets")
        if signal_day not in parsed:
            raise ValueError("Archived signal close absent from current history")
        idx = parsed.index(signal_day)
        original = snap["assets"][ticker]["signal_close"]
        if abs(prices[idx] - original) > max(1e-6, 1e-6 * original):
            raise ValueError("Archived historical price revised")
        if idx + 1 >= len(prices) or idx + 2 >= len(prices):
            pending.append(ticker)
            observed[ticker] = {"status": "PENDING_TWO_FUTURE_CLOSES"}
            continue
        entry_day, exit_day = parsed[idx + 1], parsed[idx + 2]
        if entry_day <= created_day:
            raise ValueError("Archive was generated after the simulated entry date")
        if exit_day > observed_at.date():
            raise ValueError("Future close would be used")
        if exit_day == observed_at.date() and observed_at.hour < 22:
            raise ValueError("Exit-day close might be incomplete")
        raw_return = prices[idx + 2] / prices[idx + 1] - 1
        active = snap["assets"][ticker]["signal"] == "RESEARCH_CANDIDATE"
        candidate_end = (
            _hypothetical_end(100.0, raw_return, fee_rate=fee_rate, slippage_rate=slippage_rate)
            if active else 100.0
        )
        passive_end = _hypothetical_end(
            100.0, raw_return, fee_rate=fee_rate, slippage_rate=slippage_rate)
        observed[ticker] = {
            "status": "OBSERVED",
            "archived_signal": snap["assets"][ticker]["signal"],
            "entry_close_date": entry_day.isoformat(),
            "exit_close_date": exit_day.isoformat(),
            "raw_price_return": round(raw_return, 8),
            "hypothetical_signal_equity": round(candidate_end, 6),
            "hypothetical_matched_hold_equity": round(passive_end, 6),
            "signal_minus_matched_hold": round(candidate_end - passive_end, 6),
            "signal_beat_matched_hold": candidate_end > passive_end,
        }

    complete = not pending
    return {
        **SAFE,
        "status": "OBSERVED" if complete else "PENDING",
        "signal_close_date": snap["signal_close_date"],
        "archived_at_utc": snap["generated_at_utc"],
        "strategy_version": snap["strategy_version"],
        "observations": observed,
        "observed_count": sum(v["status"] == "OBSERVED" for v in observed.values()),
        "pending_count": len(pending),
        "research_candidates_observed": sum(
            v["status"] == "OBSERVED" and v["archived_signal"] == "RESEARCH_CANDIDATE"
            for v in observed.values()),
        "comparison_fee_rate": fee_rate,
        "comparison_slippage_rate": slippage_rate,
        "limitations": (
            "Two future *dated closes* required: archived S, enter at E, score E->X; "
            "not a broker fill or real P&L. Each asset uses independent hypothetical "
            "£100 and 5% exposure, charged illustrative per-side costs. No actual "
            "spread, overnight gaps, FX, dividends, tax, order constraints or "
            "position carry between archives. No verified predictive edge."
        ),
    }


def run_pattern_forward_evaluation(document, fetcher=fetch_daily_closes, *,
                                   evaluated_at=None):
    try:
        validate_pattern_forward_snapshot(document, evaluated_at=evaluated_at)
        histories = {ticker: fetcher(ticker, period="2y") for ticker in WATCHLIST}
        return evaluate_pattern_forward_snapshot(
            document, histories, evaluated_at=evaluated_at)
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
        return {**SAFE, "status": "UNAVAILABLE",
                "error_type": type(exc).__name__,
                "reason": "Archive, chronology or market-data validation failed"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python run_pattern_forward_evaluation.py <archived_snapshot.json>")
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, ValueError):
        doc = None
    print(json.dumps(run_pattern_forward_evaluation(doc), indent=2))
