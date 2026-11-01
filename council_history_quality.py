"""Quality gates for longitudinal council decision archives.

These gates evaluate completeness and chronology, not financial performance.
"""
from datetime import date
from historical_prices import WATCHLIST

def assess_history_quality(history, *, minimum_dates=20, maximum_missing_fraction=0.2):
    if not isinstance(history, dict) or history.get("status") != "RESEARCH_ACCOUNTABILITY_HISTORY":
        raise ValueError("Invalid history report")
    if history.get("research_only") is not True or history.get("orders_allowed") is not False or history.get("live_trading_approved") is not False:
        raise ValueError("Unsafe history report")
    if type(minimum_dates) is not int or minimum_dates < 1:
        raise ValueError("Invalid minimum dates")
    if type(maximum_missing_fraction) not in (float, int) or not 0 <= maximum_missing_fraction <= 1:
        raise ValueError("Invalid missing fraction")
    timeline = history.get("timeline")
    assets = history.get("assets")
    if not isinstance(timeline, list) or not isinstance(assets, dict) or set(assets) != set(WATCHLIST):
        raise ValueError("Invalid timeline or assets")
    if history.get("selected_report_dates") != len(timeline):
        raise ValueError("Inconsistent timeline count")
    dates = []
    observed = {ticker: 0 for ticker in WATCHLIST}
    missing = {ticker: 0 for ticker in WATCHLIST}
    for day in timeline:
        if not isinstance(day, dict):
            raise ValueError("Invalid timeline day")
        stamp = day.get("date")
        if not isinstance(stamp, str) or date.fromisoformat(stamp).isoformat() != stamp:
            raise ValueError("Invalid timeline date")
        dates.append(stamp)
        rows = day.get("assets")
        if not isinstance(rows, dict) or set(rows) != set(WATCHLIST):
            raise ValueError("Invalid daily asset set")
        for ticker, row in rows.items():
            if not isinstance(row, dict):
                raise ValueError("Invalid daily entry")
            if row.get("status") == "UNAVAILABLE":
                missing[ticker] += 1
            elif row.get("status") == "OBSERVED_RESEARCH":
                if row.get("original") not in ("POSITIVE_RESEARCH", "CAUTIOUS_RESEARCH", "MIXED_RESEARCH"):
                    raise ValueError("Invalid decision label")
                if row.get("confirmed") not in ("POSITIVE_RESEARCH", "CAUTIOUS_RESEARCH", "MIXED_RESEARCH", "WAIT_FOR_CONFIRMATION"):
                    raise ValueError("Invalid confirmed label")
                if type(row.get("risk_veto")) is not bool or type(row.get("mixed_perspectives")) is not bool:
                    raise ValueError("Invalid flags")
                if row["risk_veto"] and (row["original"] != "CAUTIOUS_RESEARCH" or row["confirmed"] != "CAUTIOUS_RESEARCH"):
                    raise ValueError("Invalid veto state")
                observed[ticker] += 1
            else:
                raise ValueError("Unknown daily status")
    if dates != sorted(set(dates)):
        raise ValueError("Duplicate or unsorted dates")
    if history.get("first_date") != (dates[0] if dates else None) or history.get("last_date") != (dates[-1] if dates else None):
        raise ValueError("Incorrect date boundaries")
    for ticker, item in assets.items():
        if not isinstance(item, dict) or item.get("observations") != observed[ticker]:
            raise ValueError("Summary does not match timeline")
    issues = []
    if len(dates) < minimum_dates:
        issues.append("INSUFFICIENT_ARCHIVED_DATES")
    for ticker in WATCHLIST:
        fraction = missing[ticker] / len(dates) if dates else 1.0
        if fraction > maximum_missing_fraction:
            issues.append("EXCESS_MISSING_" + ticker)
    return {"status": "COVERAGE_OK" if not issues else "NEEDS_MORE_EVIDENCE",
            "dates": len(dates), "minimum_dates": minimum_dates,
            "maximum_missing_fraction": maximum_missing_fraction,
            "observed_by_asset": observed, "missing_by_asset": missing,
            "issues": issues, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "Coverage and integrity only; not return, prediction accuracy, independent validation or approval for live trading."}
