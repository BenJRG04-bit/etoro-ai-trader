"""Offline small-capital fee sensitivity; never orders or broker execution."""
import json
from pathlib import Path
from math import isfinite
from portfolio_benchmark import compare_portfolio_policies


def small_budget_study(prices, *, budgets=(20.0, 40.0, 100.0), fees=(0.001, 0.005)):
    if not isinstance(budgets, (tuple, list)) or not budgets:
        raise ValueError("Missing budgets")
    if any(type(b) not in (int, float) or not isfinite(b) or not 0 < b <= 100 for b in budgets):
        raise ValueError("Invalid small capital budget")
    if len(set(budgets)) != len(budgets):
        raise ValueError("Duplicate budgets")
    if not isinstance(fees, (tuple, list)) or not fees or any(type(f) not in (int, float) or not isfinite(f) or not 0 <= f < 1 for f in fees):
        raise ValueError("Invalid fees")
    scenarios = {}
    for budget in budgets:
        report = compare_portfolio_policies(prices, starting_cash=budget, fee_rates=fees)
        if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
            raise ValueError("Unsafe simulation")
        cases = {}
        for fee, row in report["scenarios"].items():
            cases[fee] = {}
            for policy in ("council_guarded", "equal_weight_capped_hold"):
                result = row[policy]
                if result.get("research_only") is not True or result.get("orders_allowed") is not False or result.get("live_trading_approved") is not False:
                    raise ValueError("Unsafe portfolio result")
                cases[fee][policy] = {
                    "starting_cash": budget, "ending_cash_equivalent": result["end_equity"],
                    "hypothetical_pnl": round(result["end_equity"] - budget, 4),
                    "max_drawdown_fraction": result["max_drawdown_fraction"],
                    "rebalance_events": result["rebalance_events"],
                    "max_observed_total_allocation": result["max_observed_total_allocation"]}
        scenarios[str(budget)] = cases
    return {"status": "EXPLORATORY_SMALL_BUDGET_ONLY", "budgets": scenarios,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "In-sample simplified fractional-position simulator. Fee sensitivity only; no minimum order size, FX conversion, spread, slippage, dividends, taxes, actual fills or broker restrictions. Hypothetical P&L is not validated forward profitability."}


if __name__ == "__main__":
    from historical_prices import WATCHLIST, fetch_daily_closes
    try:
        rows = [fetch_daily_closes(t, period="2y") for t in WATCHLIST]
        if any(row["dates"] != rows[0]["dates"] for row in rows):
            raise ValueError("DateMisalignment")
        report = small_budget_study({row["ticker"]: row["closes"] for row in rows})
    except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
        report = {"status": "UNAVAILABLE", "error_type": type(exc).__name__,
                  "research_only": True, "orders_allowed": False, "live_trading_approved": False}
    Path("small_budget_study.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
