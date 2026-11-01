"""Generate a research-only six-perspective accountability report from public prices."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from council_accountability import explain_council

def run_accountability(fetcher=fetch_daily_closes):
    assets = {}
    for ticker in WATCHLIST:
        try:
            row = fetcher(ticker, period="2y")
            if row.get("ticker") != ticker:
                raise ValueError("Ticker mismatch")
            dates, closes = row["dates"], row["closes"]
            if not dates or len(dates) != len(closes) or dates != sorted(set(dates)):
                raise ValueError("Invalid price history")
            result = explain_council(closes)
            assets[ticker] = {"status": "OBSERVED_RESEARCH", "as_of": dates[-1],
                              "close": closes[-1], "explanation": result}
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            assets[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {"status": "RESEARCH_ACCOUNTABILITY_ONLY", "assets": assets,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Public historical daily closes, six deterministic heuristics, no broker access or live orders."}

if __name__ == "__main__":
    print(json.dumps(run_accountability(), indent=2))
