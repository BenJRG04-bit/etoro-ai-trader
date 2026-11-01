"""Run offline retrospective rolling audit using aligned public daily closes."""
import json
from pathlib import Path
from historical_prices import WATCHLIST, fetch_daily_closes
from rolling_decision_audit import rolling_decision_audit, SAFE

def run():
    rows = [fetch_daily_closes(t, period="2y") for t in WATCHLIST]
    if any(row["dates"] != rows[0]["dates"] for row in rows):
        raise ValueError("Misaligned historical dates")
    report = rolling_decision_audit({row["ticker"]: row["closes"] for row in rows})
    report["source"] = "PUBLIC_HISTORICAL_CLOSES"
    return report

if __name__ == "__main__":
    try:
        result = run()
    except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
        result = {"status": "UNAVAILABLE", "error_type": type(exc).__name__, **SAFE}
    Path("rolling_decision_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"])
