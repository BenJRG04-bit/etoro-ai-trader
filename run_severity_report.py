"""Public historical prices; no brokerage access or orders."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from risk_severity import evaluate_risk_severity

def run_severity_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    assets = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker or len(history["closes"]) != len(history["dates"]):
                raise ValueError("Ticker or price/date mismatch")
            assets[ticker] = {
                "status": "EXPLORATORY_ONLY",
                "price_type": history.get("price_type", "unknown"),
                "first_date": history["dates"][0],
                "last_date": history["dates"][-1],
                "severity": evaluate_risk_severity(history["closes"]),
            }
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            assets[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {
        "mode": "OFFLINE_RISK_SEVERITY_NO_ORDERS",
        "assets": assets,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Historical associations only. Overlapping observations are not independent; no changes to trade or risk decisions.",
    }

if __name__ == "__main__":
    print(json.dumps(run_severity_report(), indent=2))
