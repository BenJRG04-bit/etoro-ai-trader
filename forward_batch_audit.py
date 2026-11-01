"""Batch audit of immutable forward snapshots, with deduplication and coverage.

The audit never replays decisions with newer data. It evaluates each archived
snapshot exactly as recorded, and separates observed from pending results.
"""
from datetime import date
from run_forward_evaluation import run_evaluation
from historical_prices import WATCHLIST

def audit_forward_snapshots(documents, fetcher, *, max_snapshots=90):
    if not isinstance(documents, list):
        raise ValueError("Snapshots must be a list")
    if not isinstance(max_snapshots, int) or not 1 <= max_snapshots <= 365:
        raise ValueError("Invalid snapshot limit")
    by_date = {}
    rejected = 0
    for doc in documents:
        if not isinstance(doc, dict) or doc.get("status") != "SNAPSHOT_RESEARCH_ONLY":
            rejected += 1
            continue
        snap = doc.get("snapshot")
        if not isinstance(snap, dict) or snap.get("schema_version") != 1:
            rejected += 1
            continue
        stamp = snap.get("snapshot_date")
        try:
            date.fromisoformat(stamp)
        except (TypeError, ValueError):
            rejected += 1
            continue
        if set(snap.get("assets", {})) != set(WATCHLIST):
            rejected += 1
            continue
        if stamp in by_date:
            if by_date[stamp] != doc:
                # Conflicting snapshots cannot be trusted: exclude date.
                by_date[stamp] = None
                rejected += 1
        else:
            by_date[stamp] = doc
    chosen = [(d, v) for d, v in sorted(by_date.items()) if v is not None][-max_snapshots:]
    results = []
    for stamp, doc in chosen:
        outcome = run_evaluation(doc, fetcher=fetcher)
        observations = (outcome.get("evaluation", {}).get("observations", {})
                        if outcome["status"] in ("OBSERVED", "PENDING") else {})
        positive = {policy: {"count": 0, "next_close_up": 0}
                    for policy in ("original", "confirmed")}
        for asset in observations.values():
            if asset.get("status") != "OBSERVED":
                continue
            for policy, key in (("original", "original_positive_at_snapshot"),
                                ("confirmed", "confirmed_positive_at_snapshot")):
                if asset.get(key):
                    positive[policy]["count"] += 1
                    if asset["next_close_return"] > 0:
                        positive[policy]["next_close_up"] += 1
        results.append({"snapshot_date": stamp, "status": outcome["status"],
                        "observed_assets": sum(x.get("status") == "OBSERVED" for x in observations.values()),
                        "pending_assets": sum(x.get("status") == "PENDING_NEW_CLOSE" for x in observations.values()),
                        "positive_signals": positive,
                        "evaluation": outcome.get("evaluation") if outcome["status"] in ("OBSERVED", "PENDING") else None,
                        "error_type": outcome.get("error_type")})
    return {"status": "RESEARCH_AUDIT", "snapshot_count": len(results),
            "rejected_snapshots": rejected,
            "observed_snapshots": sum(r["status"] == "OBSERVED" for r in results),
            "pending_snapshots": sum(r["status"] == "PENDING" for r in results),
            "unavailable_snapshots": sum(r["status"] == "UNAVAILABLE" for r in results),
            "results": results, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "Descriptive next-close directional audit, not executed P&L or a statistically validated win rate. Same-day snapshots deduplicated, conflicting versions excluded. Archive retention and missing days limit coverage."}
