"""Offline decision-quality audit: identical costs and capital for both policies."""
from math import isfinite
from portfolio_simulator import simulate_portfolio
from portfolio_benchmark import _always_eligible

SAFE = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}
COSTS = {
    "fees_only": {"fee_rate": .001},
    "illustrative_friction": {"fee_rate": .001, "spread_rate": .001,
                              "slippage_rate": .001, "fx_rate": .005, "minimum_order": 1.0},
    "high_friction": {"fee_rate": .005, "spread_rate": .005,
                      "slippage_rate": .005, "fx_rate": .01, "minimum_order": 10.0},
}

def audit_decision_quality(prices, *, budgets=(20, 40, 100),
                           scenarios=None, council_fn=None):
    scenarios = COSTS if scenarios is None else scenarios
    if not isinstance(budgets, (tuple, list)) or not budgets or len(set(budgets)) != len(budgets):
        raise ValueError("Invalid budgets")
    if any(type(x) not in (int, float) or not isfinite(x) or not 0 < x <= 100 for x in budgets):
        raise ValueError("Invalid budget")
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError("Missing cost scenarios")
    cases = {}
    for budget in budgets:
        comparison = {}
        for name, costs in scenarios.items():
            if not isinstance(name, str) or not name or not isinstance(costs, dict):
                raise ValueError("Invalid scenario")
            if set(costs) - {"fee_rate", "spread_rate", "slippage_rate", "fx_rate", "minimum_order"}:
                raise ValueError("Unsupported cost parameter")
            opts = {"starting_cash": budget, **costs}
            if council_fn is not None:
                opts["assessment_fn"] = council_fn
            council = simulate_portfolio(prices, **opts)
            baseline = simulate_portfolio(prices, **{**opts, "assessment_fn": _always_eligible})
            for result in (council, baseline):
                if any(result.get(k) is not v for k, v in SAFE.items()):
                    raise ValueError("Unsafe simulation result")
            comparison[name] = {
                "council_end_equity": council["end_equity"],
                "capped_hold_end_equity": baseline["end_equity"],
                "council_minus_capped_hold": round(council["end_equity"] - baseline["end_equity"], 4),
                "council_rebalances": council["rebalance_events"],
                "capped_hold_rebalances": baseline["rebalance_events"],
                "council_max_drawdown": council["max_drawdown_fraction"],
                "capped_hold_max_drawdown": baseline["max_drawdown_fraction"],
                "council_halted": council["halted"],
                "capped_hold_halted": baseline["halted"],
            }
        cases[str(budget)] = comparison
    return {
        "status": "IN_SAMPLE_ONLY_NO_TRADING_APPROVAL",
        "budgets": cases, "cost_scenarios": scenarios,
        "forward_validation": "NOT_ESTABLISHED",
        "live_trading_readiness": "BLOCKED",
        **SAFE,
        "limitations": "In-sample historical comparison of council vs equal-weight capped hold using the same 5% cap, "
                       "capital guard and illustrative costs. No independent forward results. Capped hold rebalances; "
                       "it is not fully invested. No actual fills or eToro fee verification.",
    }

if __name__ == "__main__":
    import json
    from pathlib import Path
    from historical_prices import WATCHLIST, fetch_daily_closes
    try:
        rows = [fetch_daily_closes(t, period="2y") for t in WATCHLIST]
        if any(row["dates"] != rows[0]["dates"] for row in rows):
            raise ValueError("Misaligned dates")
        report = audit_decision_quality({row["ticker"]: row["closes"] for row in rows})
    except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
        report = {"status": "UNAVAILABLE", "error_type": type(exc).__name__, **SAFE}
    Path("decision_quality_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
