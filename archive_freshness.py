"""Conservative freshness checks for research archive artifacts.

A recent report is not proof of profitable trading or readiness for live orders.
"""
from datetime import date

def assess_archive_freshness(history, forward, *, as_of=None, maximum_history_age_days=7,
                             maximum_forward_age_days=10):
    today = date.today() if as_of is None else date.fromisoformat(as_of)
    for limit in (maximum_history_age_days, maximum_forward_age_days):
        if type(limit) is not int or limit < 0 or limit > 365:
            raise ValueError("Invalid age limit")
    for report in (history, forward):
        if not isinstance(report, dict) or report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
            raise ValueError("Unsafe archive report")
    if history.get("status") != "RESEARCH_ACCOUNTABILITY_HISTORY" or forward.get("status") != "RESEARCH_AUDIT":
        raise ValueError("Unexpected archive status")
    if type(history.get("selected_report_dates")) is not int or history["selected_report_dates"] < 0:
        raise ValueError("Invalid history count")
    timeline = history.get("timeline")
    if not isinstance(timeline, list) or len(timeline) != history["selected_report_dates"]:
        raise ValueError("Inconsistent history dates")
    history_dates = [row["date"] for row in timeline]
    forward_rows = forward.get("results")
    if not isinstance(forward_rows, list) or len(forward_rows) != forward.get("snapshot_count"):
        raise ValueError("Inconsistent forward dates")
    forward_dates = [row["snapshot_date"] for row in forward_rows]
    def latest_age(dates):
        if not dates:
            return None
        parsed = [date.fromisoformat(value) for value in dates]
        if any(value > today for value in parsed):
            raise ValueError("Future-dated research evidence")
        return (today - max(parsed)).days
    history_age = latest_age(history_dates)
    forward_age = latest_age(forward_dates)
    if history_dates != sorted(set(history_dates)):
        raise ValueError("Unsorted or duplicate history dates")
    if len(forward_dates) != len(set(forward_dates)):
        raise ValueError("Duplicate forward dates")
    if history.get("last_date") != (history_dates[-1] if history_dates else None):
        raise ValueError("Incorrect history date boundary")
    issues = []
    if history_age is None or history_age > maximum_history_age_days:
        issues.append("HISTORY_MISSING_OR_STALE")
    if forward_age is None or forward_age > maximum_forward_age_days:
        issues.append("FORWARD_MISSING_OR_STALE")
    return {"status": "ARCHIVES_CURRENT" if not issues else "ARCHIVES_STALE_OR_MISSING",
            "as_of": today.isoformat(), "history_age_days": history_age,
            "forward_age_days": forward_age, "issues": issues,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Checks dated research availability, not trading performance or broker readiness."}
