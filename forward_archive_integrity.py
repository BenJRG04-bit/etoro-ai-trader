"""Strict structural and provenance checks for archived forward research.

Validation is deliberately fail-closed: untrusted archive content is never
converted into a trading instruction or reconstructed prediction.
"""
from datetime import date
from math import isfinite
from historical_prices import WATCHLIST

def validate_archived_snapshot(document):
    if not isinstance(document, dict) or document.get("status") != "SNAPSHOT_RESEARCH_ONLY":
        raise ValueError("Not an archived research snapshot")
    snapshot = document.get("snapshot")
    if not isinstance(snapshot, dict) or type(snapshot.get("schema_version")) is not int or snapshot["schema_version"] != 1:
        raise ValueError("Unsupported snapshot schema")
    for field, expected in (("research_only", True), ("orders_allowed", False),
                            ("live_trading_approved", False)):
        if snapshot.get(field) is not expected:
            raise ValueError("Unsafe or missing research-only flag")
    stamp = snapshot.get("snapshot_date")
    if not isinstance(stamp, str) or date.fromisoformat(stamp).isoformat() != stamp:
        raise ValueError("Invalid snapshot date")
    assets = snapshot.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(WATCHLIST):
        raise ValueError("Unexpected asset universe")
    for ticker, asset in assets.items():
        if not isinstance(asset, dict):
            raise ValueError("Invalid asset " + ticker)
        price = asset.get("close")
        if type(price) not in (float, int) or not isfinite(price) or price <= 0:
            raise ValueError("Invalid snapshot price " + ticker)
        for key in ("original_positive", "confirmed_positive", "risk_veto"):
            if type(asset.get(key)) is not bool:
                raise ValueError("Invalid decision flag " + ticker)
        if asset["risk_veto"] and asset["original_positive"]:
            raise ValueError("Risk veto contradicts original positive signal")
    return snapshot
