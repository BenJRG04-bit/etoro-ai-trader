"""Freeze price-only pattern hypotheses before later market outcomes exist.

No broker access or order submission. A snapshot produced today is ONLY
research evidence; do not treat historical thresholds as a forecast guarantee.
"""
from datetime import date, datetime, timezone
import json

from historical_prices import WATCHLIST, fetch_daily_closes
from pattern_recognition import analyze_price_patterns

VERSION = "pattern-confluence-v1"
SCHEMA_VERSION = 1


def create_pattern_forward_snapshot(histories, *, now_utc=None, watchlist=WATCHLIST):
    safe = {"research_only": True, "orders_allowed": False,
            "demo_trading_approved": False, "live_trading_approved": False}
    now = datetime.now(timezone.utc) if now_utc is None else now_utc
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Now must be a timezone-aware datetime")
    now = now.astimezone(timezone.utc)
    if (not isinstance(histories, dict) or
        not isinstance(watchlist, (tuple, list)) or
        not watchlist or len(watchlist) != len(set(watchlist)) or
        set(histories) != set(watchlist)):
        raise ValueError("Incomplete or mismatched watchlist")

    rows, common_dates = {}, None
    for ticker in sorted(watchlist):
        history = histories[ticker]
        if (not isinstance(history, dict) or history.get("ticker") != ticker
            or history.get("price_type") != "unadjusted_daily_close"):
            raise ValueError("Unknown historical price source")
        dates, closes = history.get("dates"), history.get("closes")
        if (not isinstance(dates, list) or not isinstance(closes, (list, tuple))
            or len(dates) != len(closes) or len(dates) < 250
            or not all(isinstance(s, str) for s in dates)):
            raise ValueError("Incomplete historical closes")
        converted = [date.fromisoformat(s) for s in dates]
        if (converted != sorted(set(converted)) or
            any(v.isoformat() != s for v, s in zip(converted, dates))):
            raise ValueError("Invalid historical dates")
        if common_dates is None:
            common_dates = dates
        elif dates != common_dates:
            raise ValueError("Assets must share exactly aligned close dates")
        pattern = analyze_price_patterns(closes)
        if pattern.get("status") != "OK" or (
            pattern.get("research_only") is not True or
            pattern.get("orders_allowed") is not False or
            pattern.get("live_trading_approved") is not False):
            raise ValueError("Pattern engine unavailable or unsafe")
        rows[ticker] = {
            "signal_close": float(closes[-1]),
            "signal": pattern["signal"],
            "pattern_score": pattern["pattern_score"],
            "pattern_labels": list(pattern["pattern_labels"]),
            "risk_vetoes": list(pattern["risk_vetoes"]),
        }

    close_date = date.fromisoformat(common_dates[-1])
    lag_days = (now.date() - close_date).days
    if not 0 <= lag_days <= 4:
        raise ValueError("Public close is stale or future dated")
    # US regular session normally ends by 21:00 UTC. Never freeze a possibly
    # in-progress same-day daily candle before 22:00 UTC.
    if lag_days == 0 and now.hour < 22:
        raise ValueError("Same-day close is not safely final yet")
    return {
        **safe, "schema_version": SCHEMA_VERSION,
        "strategy_version": VERSION,
        "generated_at_utc": now.isoformat(),
        "signal_close_date": common_dates[-1],
        "assets": rows,
        "source": "public_unadjusted_daily_close",
        "limitations": ("Daily closes only, no broker quotes or execution. "
                        "Signals are uncalibrated research hypotheses; "
                        "archive timestamps and future outcomes must be checked independently."),
    }


def run_pattern_forward_snapshot(fetcher=fetch_daily_closes, *,
                                 tickers=WATCHLIST, period="2y", now_utc=None):
    safe = {"research_only": True, "orders_allowed": False,
            "demo_trading_approved": False, "live_trading_approved": False}
    try:
        if set(tickers) != set(WATCHLIST) or len(tickers) != len(WATCHLIST):
            raise ValueError("Unexpected watchlist")
        histories = {ticker: fetcher(ticker, period=period) for ticker in tickers}
        snapshot = create_pattern_forward_snapshot(
            histories, now_utc=now_utc, watchlist=tickers)
        return {**safe, "status": "PATTERN_SNAPSHOT_RESEARCH_ONLY",
                "snapshot": snapshot}
    except (ValueError, TypeError, KeyError, OSError, IndexError, OverflowError) as exc:
        return {**safe, "status": "UNAVAILABLE",
                "error_type": type(exc).__name__}


if __name__ == "__main__":
    print(json.dumps(run_pattern_forward_snapshot(), indent=2))
