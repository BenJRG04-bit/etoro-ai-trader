"""Conservative operational health checks for the forward research archive.

Health is not strategy performance, a trading signal, or live-trading approval.
"""
from datetime import date

def assess_archive_health(audit, quality, *, minimum_observed=20, maximum_pending_fraction=0.5):
    if not isinstance(audit, dict) or audit.get("status") != "RESEARCH_AUDIT":
        raise ValueError("Invalid archive audit")
    if not isinstance(quality, dict) or quality.get("status") != "RESEARCH_EVIDENCE_ONLY":
        raise ValueError("Invalid evidence report")
    for source in (audit, quality):
        if source.get("research_only") is not True or source.get("orders_allowed") is not False or source.get("live_trading_approved") is not False:
            raise ValueError("Unsafe research report")
    if type(minimum_observed) is not int or minimum_observed < 1:
        raise ValueError("Invalid minimum observations")
    if type(maximum_pending_fraction) not in (int, float) or not 0 <= maximum_pending_fraction <= 1:
        raise ValueError("Invalid pending threshold")
    entries = audit.get("results")
    if not isinstance(entries, list):
        raise ValueError("Missing archive results")
    dates = set()
    observed = pending = unavailable = 0
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("Malformed archive result")
        stamp = item.get("snapshot_date")
        if not isinstance(stamp, str) or date.fromisoformat(stamp).isoformat() != stamp or stamp in dates:
            raise ValueError("Duplicate or invalid snapshot date")
        dates.add(stamp)
        status = item.get("status")
        if status == "OBSERVED":
            observed += 1
        elif status == "PENDING":
            pending += 1
        elif status == "UNAVAILABLE":
            unavailable += 1
        else:
            raise ValueError("Unknown archive status")
    if observed != audit.get("observed_snapshots") or pending != audit.get("pending_snapshots") or unavailable != audit.get("unavailable_snapshots"):
        raise ValueError("Inconsistent archive totals")
    if len(entries) != audit.get("snapshot_count"):
        raise ValueError("Inconsistent snapshot count")
    if observed != quality.get("observed_snapshot_dates"):
        raise ValueError("Evidence and audit coverage disagree")
    total = len(entries)
    pending_fraction = pending / total if total else None
    checks = {
        "has_archived_snapshots": total > 0,
        "minimum_observed_snapshots": observed >= minimum_observed,
        "pending_fraction_acceptable": pending_fraction is not None and pending_fraction <= maximum_pending_fraction,
        "no_unavailable_snapshots": unavailable == 0,
        "no_rejected_snapshots": audit.get("rejected_snapshots") == 0,
    }
    issues = [key for key, ok in checks.items() if not ok]
    return {"status": "COVERAGE_OK" if not issues else "NEEDS_MORE_EVIDENCE",
            "checks": checks, "issues": issues, "total_snapshots": total,
            "observed_snapshots": observed, "pending_snapshots": pending,
            "unavailable_snapshots": unavailable,
            "pending_fraction": round(pending_fraction, 4) if pending_fraction is not None else None,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Archive availability/coverage checks only; COVERAGE_OK is not statistical validation, profit evidence, or permission to trade."}
