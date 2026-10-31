"""Generate actual-history evaluation reports; no order placement."""
import json
from datetime import datetime, timezone
from historical_prices import WATCHLIST, fetch_daily_closes
from historical_evaluation import evaluate_windows

def build_historical_report(period="2y", test_size=60):
    results = {}
    for ticker in WATCHLIST:
        try:
            series = fetch_daily_closes(ticker, period)
            analysis = evaluate_windows(series["closes"], test_size=test_size)
            # Date annotations align with each test interval; no future data used.
            for window in analysis["windows"]:
                window["start_date"] = series["dates"][window["test_start_index"]]
                window["end_date"] = series["dates"][window["test_end_index_exclusive"] - 1]
            results[ticker] = {"status": "OK", "price_type": series["price_type"],
                               "observations": len(series["closes"]), "evaluation": analysis}
        except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
            results[ticker] = {"status": "DATA_OR_EVALUATION_ERROR",
                               "reason": str(exc)}
    return {"mode": "PUBLIC_DATA_OFFLINE_EVALUATION_NO_ORDERS",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "period": period, "test_size": test_size, "assets": results,
            "research_only": True,
            "limitations": ("Unadjusted daily closes: splits/dividends may distort comparisons. "
                            "Public data can be delayed or incomplete. In-sample illustrative "
                            "evaluation, not proof of profitability or live readiness.")}

if __name__ == "__main__":
    print(json.dumps(build_historical_report(), indent=2))
