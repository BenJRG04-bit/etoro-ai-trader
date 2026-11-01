"""Fail-closed provenance checks for archived prospective research snapshots."""
from datetime import date, datetime, timezone

def check_snapshot_provenance(document, *, observed_at=None, minimum_age_days=1):
    if type(minimum_age_days) is not int or minimum_age_days < 1:
        raise ValueError("Invalid minimum age")
    if not isinstance(document, dict) or document.get("status") != "SNAPSHOT_RESEARCH_ONLY":
        raise ValueError("Not an archived research snapshot")
    if document.get("research_only") is not True or document.get("orders_allowed") is not False or document.get("live_trading_approved") is not False:
        raise ValueError("Unsafe snapshot")
    snap = document.get("snapshot")
    if not isinstance(snap, dict):
        raise ValueError("Missing snapshot")
    raw = snap.get("snapshot_date")
    if not isinstance(raw, str):
        raise ValueError("Missing historical close date")
    try:
        snapshot_date = date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("Invalid historical close date") from exc
    if observed_at is None:
        observed_at = datetime.now(timezone.utc).date()
    if not isinstance(observed_at, date) or isinstance(observed_at, datetime):
        raise ValueError("Invalid observation date")
    age = (observed_at - snapshot_date).days
    if age < minimum_age_days:
        return {"status": "PENDING", "reason": "INSUFFICIENT_ELAPSED_DAYS",
                "snapshot_date": raw, "age_days": age,
                "research_only": True, "orders_allowed": False, "live_trading_approved": False}
    return {"status": "ELIGIBLE_FOR_FORWARD_EVALUATION", "snapshot_date": raw,
            "age_days": age, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "Elapsed calendar days do not establish an observed newer market close. "
                           "The evaluator must independently require newer dated prices. "
                           "Artifact authenticity and immutable archive validation remain separate checks."}
