"""Public historical market-data runner for fixed-policy comparisons."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from strategy_evaluation import evaluate_strategies

def run_strategy_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    assets = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker or len(history["dates"]) != len(history["closes"]):
                raise ValueError("Ticker/date mismatch")
            result = evaluate_strategies(history["closes"])
            assets[ticker] = {
                "status": "EXPLORATORY_ONLY",
                "split_date": history["dates"][result["split_price_index"]],
                "price_type": history.get("price_type", "unknown"),
                "evaluation": result,
            }
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            assets[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {
        "mode": "OFFLINE_V04_FIXED_STRATEGY_RESEARCH",
        "assets": assets,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Independent £100-per-asset historical tests, not a combined portfolio. No live trading or autonomous strategy changes.",
    }

if __name__ == "__main__":
    print(json.dumps(run_strategy_report(), indent=2))
