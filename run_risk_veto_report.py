"""Read-only historical risk warning outcome report. No broker connections."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from risk_veto_outcomes import evaluate_risk_vetoes

def run_risk_veto_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    assets = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker:
                raise ValueError("Ticker mismatch")
            assets[ticker] = {
                "status": "EXPLORATORY_ONLY",
                "outcomes": evaluate_risk_vetoes(history["closes"]),
                "first_date": history["dates"][0],
                "last_date": history["dates"][-1],
            }
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            assets[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {
        "mode": "OFFLINE_RISK_VETO_REPORT",
        "assets": assets,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Next-day historical associations, not proof of avoided losses or future predictive accuracy. No parameter tuning.",
    }

if __name__ == "__main__":
    print(json.dumps(run_risk_veto_report(), indent=2))
