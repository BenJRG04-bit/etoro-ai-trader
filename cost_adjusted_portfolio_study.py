"""Historical paired friction sensitivity, offline only and no broker orders."""
from math import isfinite
from portfolio_simulator import simulate_portfolio
from portfolio_benchmark import _always_eligible

SAFE = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}

def compare_cost_assumptions(prices, *, budgets=(20, 40, 100),
                             assumptions=None, assessment_fn=None):
    if assumptions is None:
        assumptions = {
            "base_fees_only": {"fee_rate": .001},
            "illustrative_friction": {"fee_rate": .001, "spread_rate": .001,
                                      "slippage_rate": .001, "fx_rate": .005,
                                      "minimum_order": 1.0},
            "high_friction": {"fee_rate": .005, "spread_rate": .005,
                              "slippage_rate": .005, "fx_rate": .01,
                              "minimum_order": 10.0},
        }
    if not isinstance(budgets, (tuple, list)) or not budgets or len(set(budgets)) != len(budgets):
        raise ValueError("Invalid budgets")
    if any(type(b) not in (int, float) or not isfinite(b) or not 0 < b <= 100 for b in budgets):
        raise ValueError("Invalid budget")
    if not isinstance(assumptions, dict) or "base_fees_only" not in assumptions:
        raise ValueError("Missing baseline assumptions")
    for name, params in assumptions.items():
        if not isinstance(name, str) or not name or not isinstance(params, dict):
            raise ValueError("Invalid assumptions")
        if set(params) - {"fee_rate", "spread_rate", "slippage_rate", "fx_rate", "minimum_order"}:
            raise ValueError("Unsupported cost parameter")
    results = {}
    for budget in budgets:
        cases = {}
        for name, params in assumptions.items():
            opts = {"starting_cash": budget, **params}
            if assessment_fn is not None:
                opts["assessment_fn"] = assessment_fn
            result = simulate_portfolio(prices, **opts)
            if any(result.get(k) is not v for k, v in SAFE.items()):
                raise ValueError("Unsafe simulation")
            cases[name] = {
                "ending_equity": result["end_equity"],
                "hypothetical_pnl": round(result["end_equity"] - budget, 4),
                "rebalance_events": result["rebalance_events"],
                "max_drawdown_fraction": result["max_drawdown_fraction"],
                "max_observed_total_allocation": result["max_observed_total_allocation"],
                "halted": result["halted"],
            }
        baseline = cases["base_fees_only"]["ending_equity"]
        for row in cases.values():
            row["ending_equity_vs_base_fees_only"] = round(row["ending_equity"] - baseline, 4)
        results[str(budget)] = cases
    return {"status": "IN_SAMPLE_COST_SENSITIVITY_ONLY", "budgets": results,
            "assumptions": assumptions, **SAFE,
            "limitations": "Retrospective close-based scenario study. Costs and minimum sizes are illustrative, not verified broker terms. "
                           "Higher minimums can suppress trades, so results need not monotonically decline with costs. "
                           "No independent forward profitability or actual execution."}

if __name__ == "__main__":
    import json
    from pathlib import Path
    from historical_prices import WATCHLIST, fetch_daily_closes
    try:
        rows = [fetch_daily_closes(t, period="2y") for t in WATCHLIST]
        if any(row["dates"] != rows[0]["dates"] for row in rows):
            raise ValueError("Misaligned dates")
        report = compare_cost_assumptions({row["ticker"]: row["closes"] for row in rows})
    except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
        report = {"status": "UNAVAILABLE", "error_type": type(exc).__name__, **SAFE}
    Path("cost_adjusted_portfolio_study.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
