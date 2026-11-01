"""Public-data pattern research runner; no API keys, brokerage access or orders.

Every asset produces a dated hypothesis and a chronological, cost-stressed
comparison. Stale public prices never produce an actionable-looking preview.
"""
import json
from datetime import date, datetime, timezone

from historical_prices import WATCHLIST, fetch_daily_closes
from pattern_recognition import analyze_price_patterns
from pattern_strategy_evaluation import evaluate_pattern_strategies


def run_pattern_research(fetcher=fetch_daily_closes, tickers=WATCHLIST,
                         period="2y", now_utc=None):
    now = datetime.now(timezone.utc) if now_utc is None else now_utc
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Timezone-aware current time required")
    if not isinstance(tickers, (tuple, list)) or not tickers or len(tickers) != len(set(tickers)):
        raise ValueError("Expected distinct nonempty watchlist")
    records = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if not isinstance(history, dict) or history.get("ticker") != ticker:
                raise ValueError("Incorrect market history")
            dates, closes = history["dates"], history["closes"]
            if not isinstance(dates, list) or len(dates) != len(closes):
                raise ValueError("Date alignment failed")
            parsed = [date.fromisoformat(value) for value in dates]
            if not parsed or parsed != sorted(set(parsed)):
                raise ValueError("Invalid or unsorted dates")
            lag_days = (now.date() - parsed[-1]).days
            # Source may be delayed or markets closed; no guessing intraday freshness.
            fresh = 0 <= lag_days <= 4
            pattern = analyze_price_patterns(closes)
            evaluation = evaluate_pattern_strategies(closes)
            records[ticker] = {
                "status": "EXPLORATORY_ONLY" if fresh else "STALE_PUBLIC_DATA",
                "as_of_date": dates[-1],
                "price_type": history.get("price_type", "unknown"),
                "days_since_last_close": lag_days,
                "latest_pattern": pattern if fresh else {
                    "status": "STALE_PUBLIC_DATA",
                    "signal": "NO_CANDIDATE",
                    "research_only": True, "orders_allowed": False,
                },
                "historical_comparison": evaluation,
            }
        except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
            records[ticker] = {
                "status": "UNAVAILABLE", "error_type": type(exc).__name__,
                "latest_pattern": {"signal": "NO_CANDIDATE"},
            }
    return {
        "mode": "DAILY_PATTERN_RESEARCH_NO_ORDERS",
        "generated_at_utc": now.astimezone(timezone.utc).isoformat(),
        "assets": records,
        "research_only": True, "orders_allowed": False,
        "demo_trading_approved": False, "live_trading_approved": False,
        "limitations": (
            "Daily public close prices, not live quotes or verified broker eligibility. "
            "Pattern labels are fixed, correlated heuristic signals, not forecasts. "
            "Retrospective later segments already examined and not independent new "
            "validation. Fees/slippage illustrative; no eToro demo or real orders."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_pattern_research(), indent=2))
