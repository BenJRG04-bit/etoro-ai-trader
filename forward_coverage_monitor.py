"""Conservative coverage and integrity summary of archived forward observations.

Descriptive monitoring only. Does not turn historical results into trading approval.
"""
from datetime import date

SAFE = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}

def summarize_forward_coverage(audit):
    if not isinstance(audit, dict) or audit.get("status") != "RESEARCH_AUDIT":
        raise ValueError("Missing forward batch audit")
    if any(audit.get(k) is not v for k, v in SAFE.items()):
        raise ValueError("Unsafe forward audit")
    results = audit.get("results")
    if not isinstance(results, list):
        raise ValueError("Invalid forward observations")
    seen = set()
    observed_dates = []
    counts = {"OBSERVED": 0, "PENDING": 0, "UNAVAILABLE": 0}
    for row in results:
        if not isinstance(row, dict) or row.get("status") not in counts:
            raise ValueError("Invalid observation status")
        stamp = row.get("snapshot_date")
        if not isinstance(stamp, str) or date.fromisoformat(stamp).isoformat() != stamp or stamp in seen:
            raise ValueError("Invalid or duplicate observation date")
        seen.add(stamp)
        counts[row["status"]] += 1
        if row["status"] == "OBSERVED":
            observed_dates.append(stamp)
    if audit.get("snapshot_count") != len(results):
        raise ValueError("Snapshot count mismatch")
    for key, expected in (("observed_snapshots", counts["OBSERVED"]),
                          ("pending_snapshots", counts["PENDING"]),
                          ("unavailable_snapshots", counts["UNAVAILABLE"])):
        if audit.get(key) != expected:
            raise ValueError("Forward count mismatch")
    rejected = audit.get("rejected_snapshots")
    if type(rejected) is not int or rejected < 0:
        raise ValueError("Invalid rejected count")
    blockers = []
    if not observed_dates:
        blockers.append("NO_OBSERVED_FORWARD_DATES")
    if len(observed_dates) < 20:
        blockers.append("INSUFFICIENT_OBSERVED_DATES")
    if counts["UNAVAILABLE"]:
        blockers.append("UNAVAILABLE_FORWARD_EVALUATIONS")
    if rejected:
        blockers.append("REJECTED_ARCHIVED_SNAPSHOTS")
    return {
        "status": "DESCRIPTIVE_FORWARD_COVERAGE_ONLY",
        "observed_dates": len(observed_dates),
        "first_observed_date": min(observed_dates) if observed_dates else None,
        "last_observed_date": max(observed_dates) if observed_dates else None,
        "pending_dates": counts["PENDING"],
        "unavailable_dates": counts["UNAVAILABLE"],
        "rejected_snapshots": rejected,
        "blockers": blockers,
        "forward_validation": "NOT_ESTABLISHED",
        "live_trading_readiness": "BLOCKED",
        **SAFE,
        "limitations": "Coverage and integrity counts only. 20 dates is a monitoring threshold, not a statistical "
                       "power calculation or approval criterion. Observations may be correlated and incomplete.",
    }
