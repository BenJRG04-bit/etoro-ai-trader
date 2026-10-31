"""Audit public historical price series before offline strategy evaluation.

No brokerage access or orders. Unadjusted closes are not total returns.
"""
from datetime import date
from math import isfinite


def audit_history(data, min_observations=120):
    if not isinstance(min_observations, int) or min_observations < 120:
        raise ValueError("Minimum observations must be at least 120")
    if not isinstance(data, dict):
        raise ValueError("Expected historical price record")
    dates, closes = data.get("dates"), data.get("closes")
    if not isinstance(dates, list) or not isinstance(closes, list):
        raise ValueError("Dates and closes must be lists")
    if len(dates) != len(closes) or len(dates) < min_observations:
        raise ValueError("Insufficient or mismatched observations")
    previous = None
    for day, price in zip(dates, closes):
        if not isinstance(day, str):
            raise ValueError("Invalid date")
        parsed = date.fromisoformat(day)
        if previous is not None and parsed <= previous:
            raise ValueError("Dates must be strictly increasing")
        previous = parsed
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError("Invalid price type")
        if not isfinite(price) or price <= 0:
            raise ValueError("Prices must be positive and finite")
    if data.get("price_type") != "unadjusted_daily_close":
        raise ValueError("Unknown price adjustment status")
    return {
        "ticker": data.get("ticker"),
        "observation_count": len(closes),
        "first_date": dates[0],
        "last_date": dates[-1],
        "valid_for_exploratory_research": True,
        "valid_for_total_return_comparison": False,
        "live_trading_approved": False,
        "research_only": True,
        "warning": ("Unadjusted closes omit dividends and may distort "
                    "split-related returns. Obtain validated adjusted "
                    "prices and corporate actions before drawing "
                    "performance conclusions.")
    }
