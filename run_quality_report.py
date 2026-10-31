"""Offline evidence quality report across public historical watchlist data."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from holdout_risk_audit import audit_holdout
from evidence_quality import assess_evidence_quality

def run_quality_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    assets = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker or len(history["closes"]) != len(history["dates"]):
                raise ValueError("Ticker/date mismatch")
            audit = audit_holdout(history["closes"])
            quality = assess_evidence_quality(audit)
            assets[ticker] = {
                "status": "EXPLORATORY_ONLY",
                "sample_adequate": quality["all_horizons_sample_adequate"],
                "quality": quality,
                "split_date": history["dates"][audit["split_price_index"]],
                "price_type": history.get("price_type", "unknown"),
            }
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            assets[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {
        "mode": "EVIDENCE_QUALITY_OFFLINE",
        "assets": assets,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Sample checks only. No trading readiness or strategy performance certification.",
    }

if __name__ == "__main__":
    print(json.dumps(run_quality_report(), indent=2))
