"""Stress-test trading friction without orders or broker access.

Each rebalance incurs a simple per-side commission plus half-spread and
slippage, applied to turnover. These are assumptions, not broker quotes.
"""
from math import isfinite
from six_brains import council
from regime_council import regime_aware_council

def friction_backtest(closes, *, assessment_fn=None, starting_cash=1000.0,
                      commission_rate=0.001, spread_rate=0.002,
                      slippage_rate=0.001, max_allocation=0.05):
    if len(closes) < 62 or any(not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Need at least 62 valid positive closes")
    if not isfinite(starting_cash) or starting_cash <= 0:
        raise ValueError("Invalid starting cash")
    for x in (commission_rate, spread_rate, slippage_rate, max_allocation):
        if not isfinite(x) or x < 0:
            raise ValueError("Costs and allocation must be finite nonnegative")
    if max_allocation > 0.05 or commission_rate >= 1 or spread_rate >= 1 or slippage_rate >= 1:
        raise ValueError("Costs or allocation outside research limits")
    assessment_fn = assessment_fn or council
    equity, peak, position = starting_cash, starting_cash, 0.0
    curve = [equity]
    rebalance_events = 0
    cumulative_cost = 0.0
    stopped = False
    cost_per_turnover = commission_rate + spread_rate / 2 + slippage_rate
    for t in range(59, len(closes) - 1):
        decision = assessment_fn(closes[:t + 1])["decision"]
        desired = max_allocation if decision == "POSITIVE_RESEARCH" else 0.0
        if stopped or equity <= peak * 0.9:
            stopped = True
            desired = 0.0
        turnover = abs(desired - position)
        if turnover > 1e-12:
            cost = equity * turnover * cost_per_turnover
            equity -= cost
            cumulative_cost += cost
            rebalance_events += 1
        position = desired
        equity *= 1 + position * (closes[t + 1] / closes[t] - 1)
        peak = max(peak, equity)
        curve.append(equity)
    max_dd = 0.0
    high = curve[0]
    for value in curve:
        high = max(high, value)
        max_dd = max(max_dd, (high - value) / high)
    return {
        "mode": "FRICTION_STRESS_TEST_NO_ORDERS",
        "end_equity": round(equity, 4),
        "return_fraction": round(equity / starting_cash - 1, 6),
        "max_drawdown_fraction": round(max_dd, 6),
        "rebalance_events": rebalance_events,
        "estimated_friction_paid": round(cumulative_cost, 4),
        "assumptions": {"commission_rate": commission_rate,
                        "spread_rate": spread_rate, "slippage_rate": slippage_rate,
                        "max_allocation": max_allocation},
        "stopped": stopped, "research_only": True,
        "limitations": "Simplified turnover costs, no minimum commissions, taxes, FX, dividends, order-book or execution simulation."
    }

def compare_friction_scenarios(closes, *, starting_cash=1000.0, max_allocation=0.05):
    scenarios = {
        "optimistic": (0.0, 0.0005, 0.0005),
        "moderate": (0.001, 0.002, 0.001),
        "pessimistic": (0.003, 0.006, 0.003),
    }
    return {"mode": "FRICTION_SCENARIO_COMPARISON_NO_ORDERS",
            "scenarios": {name: {
                "baseline": friction_backtest(
                    closes, starting_cash=starting_cash, max_allocation=max_allocation,
                    commission_rate=commission, spread_rate=spread,
                    slippage_rate=slippage),
                "risk_aware": friction_backtest(
                    closes, assessment_fn=regime_aware_council,
                    starting_cash=starting_cash, max_allocation=max_allocation,
                    commission_rate=commission, spread_rate=spread,
                    slippage_rate=slippage)
            } for name, (commission, spread, slippage) in scenarios.items()},
            "research_only": True}
