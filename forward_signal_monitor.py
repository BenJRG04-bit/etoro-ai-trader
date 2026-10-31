"""Research-only forward signal snapshots and later evaluation.

Snapshots contain decisions made using closes available on the snapshot date.
A later evaluation requires an explicitly provided, older snapshot and newer
market data. Neither action trades or changes strategy settings.
"""
from datetime import date
from math import isfinite
from regime_council import regime_aware_council
from decision_confirmation_experiment import confirmed_assessment

def create_signal_snapshot(histories, assessment_fn=regime_aware_council):
    if not isinstance(histories, dict) or not histories:
        raise ValueError("Missing histories")
    tickers = sorted(histories)
    dates = None
    rows = {}
    for ticker in tickers:
        row = histories[ticker]
        d, closes = row["dates"], row["closes"]
        if (not isinstance(ticker, str) or not ticker or len(d) != len(closes)
                or len(d) < 62 or d != sorted(set(d))):
            raise ValueError("Invalid history")
        if any(type(v) not in (int, float) or not isfinite(v) or v <= 0 for v in closes):
            raise ValueError("Invalid close")
        if dates is None:
            dates = d
        elif dates != d:
            raise ValueError("DateMisalignment")
        original = assessment_fn(closes)
        confirmed = confirmed_assessment(closes, assessment_fn)
        if not isinstance(original, dict) or not isinstance(confirmed, dict):
            raise ValueError("Invalid assessment")
        rows[ticker] = {
            "close": closes[-1],
            "original_positive": original.get("status") == "OK" and
                original.get("decision") == "POSITIVE_RESEARCH" and
                not original.get("regime_risk_veto", False),
            "confirmed_positive": confirmed.get("status") == "OK" and
                confirmed.get("decision") == "POSITIVE_RESEARCH" and
                not confirmed.get("regime_risk_veto", False),
            "risk_veto": bool(original.get("regime_risk_veto", False)),
        }
    return {"schema_version": 1, "snapshot_date": dates[-1],
            "assets": rows, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "Signals frozen at most recent available public daily close. Prices unadjusted; no FX, dividends, execution or profit forecast."}

def evaluate_snapshot(snapshot, histories):
    if snapshot.get("schema_version") != 1 or not snapshot.get("research_only"):
        raise ValueError("Invalid snapshot")
    if not isinstance(histories, dict) or set(histories) != set(snapshot["assets"]):
        raise ValueError("Asset mismatch")
    snapshot_date = snapshot["snapshot_date"]
    date.fromisoformat(snapshot_date)
    observations = {}
    for ticker, old in snapshot["assets"].items():
        row = histories[ticker]
        dates, closes = row["dates"], row["closes"]
        if (len(dates) != len(closes) or dates != sorted(set(dates))
                or snapshot_date not in dates):
            raise ValueError("Missing snapshot date or invalid history")
        index = dates.index(snapshot_date)
        if abs(closes[index] - old["close"]) > max(1e-6, abs(old["close"]) * 1e-6):
            raise ValueError("Historical close revised; cannot compare safely")
        if index + 1 >= len(dates):
            observations[ticker] = {"status": "PENDING_NEW_CLOSE"}
            continue
        newer = closes[index + 1]
        if type(newer) not in (int, float) or not isfinite(newer) or newer <= 0:
            raise ValueError("Invalid future close")
        observations[ticker] = {
            "status": "OBSERVED",
            "next_date": dates[index + 1],
            "next_close_return": round(newer / old["close"] - 1, 8),
            "original_positive_at_snapshot": old["original_positive"],
            "confirmed_positive_at_snapshot": old["confirmed_positive"],
            "risk_veto_at_snapshot": old["risk_veto"],
        }
    return {"snapshot_date": snapshot_date, "observations": observations,
            "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "One next-close observation only; not an executed trade, net P&L, independent statistical proof or forecast. Missing new closes remain pending."}
