"""Run chronological risk warning audit on public prices only."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from holdout_risk_audit import audit_holdout

def run_holdout_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    assets = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker or len(history["dates"]) != len(history["closes"]):
                raise ValueError("Price/date or ticker mismatch")
            audit = audit_holdout(history["closes"])
            split = audit["split_price_index"]
            assets[ticker] = {
                "status": "EXPLORATORY_ONLY",
                "price_type": history.get("price_type", "unknown"),
                "earlier_end_date": history["dates"][split - 1],
                "later_start_date": history["dates"][split],
                "audit": audit,
            }
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            assets[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {
        "mode": "OFFLINE_HOLDOUT_RISK_AUDIT",
        "assets": assets,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
    }

if __name__ == "__main__":
    print(json.dumps(run_holdout_report(), indent=2))
