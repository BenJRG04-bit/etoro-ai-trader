"""Research-only historical evaluation pipeline for the existing watchlist.

Uses public, unadjusted daily closes; results are exploratory, not total returns.
Never sends orders or uses brokerage credentials.
"""
from historical_prices import WATCHLIST, fetch_daily_closes
from historical_data_audit import audit_history
from historical_evaluation import evaluate_windows


def run_historical_research(fetcher=fetch_daily_closes, period="2y",
                            test_size=60):
    if period not in ("1y", "2y", "5y"):
        raise ValueError("Unsupported history period")
    if not isinstance(test_size, int) or isinstance(test_size, bool) or test_size < 2:
        raise ValueError("test_size must be an integer >= 2")
    results = {}
    for ticker in WATCHLIST:
        try:
            history = fetcher(ticker, period=period)
            if history.get("ticker") != ticker:
                raise ValueError("Historical data ticker does not match request")
            audit = audit_history(history)
            evaluation = evaluate_windows(history["closes"], test_size=test_size)
            results[ticker] = {
                "status": "EXPLORATORY_ONLY",
                "data_audit": audit,
                "evaluation": evaluation,
            }
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            results[ticker] = {
                "status": "DATA_OR_EVALUATION_UNAVAILABLE",
                "error_type": type(exc).__name__,
            }
    return {
        "mode": "HISTORICAL_RESEARCH_NO_ORDERS",
        "assets": results,
        "research_only": True,
        "live_trading_approved": False,
        "limitations": (
            "Public unadjusted closes may misstate performance around splits "
            "and omit dividends. Historical windows are not necessarily "
            "untouched out-of-sample data. Simplified costs; no live orders."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_historical_research(), indent=2))
