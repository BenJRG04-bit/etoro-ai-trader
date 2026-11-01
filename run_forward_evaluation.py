"""Evaluate an archived research snapshot using strictly newer public closes.

Input is an existing, immutable GitHub Actions snapshot JSON downloaded by
the workflow. Never re-create a past signal from newer data.
"""
import json
import sys
from historical_prices import WATCHLIST, fetch_daily_closes
from forward_signal_monitor import evaluate_snapshot
from forward_archive_integrity import validate_archived_snapshot
from forward_provenance_gate import check_snapshot_provenance

def run_evaluation(snapshot_document, fetcher=fetch_daily_closes):
    unavailable = {"status": "UNAVAILABLE", "research_only": True,
                   "orders_allowed": False, "live_trading_approved": False}
    if not isinstance(snapshot_document, dict) or snapshot_document.get("status") != "SNAPSHOT_RESEARCH_ONLY":
        return dict(unavailable, error_type="InvalidSnapshot")
    try:
        snap = validate_archived_snapshot(snapshot_document)
    except (ValueError, TypeError, KeyError):
        return dict(unavailable, error_type="InvalidArchivedSnapshot")
    try:
        provenance = check_snapshot_provenance(snapshot_document)
    except (ValueError, TypeError):
        return dict(unavailable, error_type='InvalidSnapshotProvenance')
    if provenance['status'] != 'ELIGIBLE_FOR_FORWARD_EVALUATION':
        return {'status': 'PENDING', 'reason': provenance['reason'],
                'research_only': True, 'orders_allowed': False, 'live_trading_approved': False}
    histories = {}
    for ticker in WATCHLIST:
        try:
            row = fetcher(ticker, period="2y")
            if row["ticker"] != ticker:
                raise ValueError("Ticker mismatch")
            histories[ticker] = row
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            return dict(unavailable, error_type=type(exc).__name__, failed_ticker=ticker)
    try:
        result = evaluate_snapshot(snap, histories)
    except (ValueError, TypeError, KeyError) as exc:
        return dict(unavailable, error_type=type(exc).__name__)
    statuses = {v["status"] for v in result["observations"].values()}
    return {"status": "OBSERVED" if statuses == {"OBSERVED"} else "PENDING",
            "evaluation": result, "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python run_forward_evaluation.py <archived_snapshot.json>")
    with open(sys.argv[1], encoding="utf-8") as handle:
        document = json.load(handle)
    print(json.dumps(run_evaluation(document), indent=2))
