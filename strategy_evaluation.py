"""Version 0.4: fixed-policy, chronological offline strategy evaluation.

Strategies are hypotheses fixed before looking at the later period, NOT
optimized or auto-selected for live trading.
"""
from math import isfinite
from backtest import backtest
from regime_council import regime_aware_council

POLICIES = ("council_guarded", "trend_guarded", "capped_hold")

def _assessment(prices, policy):
    current = regime_aware_council(prices)
    blocked = current.get("status") != "OK" or current.get("regime_risk_veto") or current.get("market_regime") in ("HIGH_RISK", "INSUFFICIENT_DATA")
    if policy == "capped_hold":
        positive = True
    elif policy == "trend_guarded":
        positive = not blocked and current["market_regime"] == "UPTREND"
    else:
        positive = not blocked and current["decision"] == "POSITIVE_RESEARCH"
    return {"decision": "POSITIVE_RESEARCH" if positive else "CAUTIOUS_RESEARCH"}

def evaluate_strategies(closes, holdout_fraction=0.30, fee_rates=(0.001, 0.005)):
    if not isinstance(closes, (list, tuple)) or len(closes) < 200:
        raise ValueError("At least 200 prices required")
    if any(type(x) not in (float, int) or not isfinite(x) or x <= 0 for x in closes):
        raise ValueError("Prices must be positive and finite")
    if type(holdout_fraction) not in (int, float) or not 0.2 <= holdout_fraction <= 0.5:
        raise ValueError("Holdout fraction must be 0.2 to 0.5")
    if not isinstance(fee_rates, (tuple, list)) or not fee_rates or any(type(f) not in (float, int) or not isfinite(f) or not 0 <= f < 0.1 for f in fee_rates):
        raise ValueError("Invalid fee scenarios")
    split = int(len(closes) * (1 - holdout_fraction))
    if split < 62 or len(closes) - split < 62:
        raise ValueError("Insufficient history in each period")
    # Later-period decisions may use 59 warmup closes from the earlier period.
    # The backtest starts at t=59 and its first scored return is split -> split+1.
    periods = {
        "earlier": closes[:split + 1],
        "later_holdout": closes[split - 59:],
    }
    results = {}
    for name, prices in periods.items():
        scenarios = {}
        for fee in fee_rates:
            policies = {}
            for policy in POLICIES:
                result = backtest(
                    prices, starting_cash=100.0, fee_rate=fee, max_allocation=0.05,
                    assessment_fn=lambda past, p=policy: _assessment(past, p),
                    use_capital_guard=True,
                )
                policies[policy] = {
                    "end_equity": result["end_equity"],
                    "return_fraction": result["return_fraction"],
                    "max_drawdown_fraction": result["max_drawdown_fraction"],
                    "rebalance_events": result["rebalance_events"],
                    "halted": result["stopped"],
                }
            scenarios[str(fee)] = policies
        results[name] = {"scenarios": scenarios, "scored_return_periods": len(prices) - 60}
    return {
        "mode": "OFFLINE_FIXED_POLICY_CHRONOLOGICAL_COMPARISON",
        "split_price_index": split,
        "policies": list(POLICIES),
        "segments": results,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Fixed retrospective strategy comparison, not independent validation after viewing holdout. Later period has 59 prior warmup closes; no scored return crosses the split. 5% per-asset cap, simplified fees, no FX, dividends, spread, slippage or tax. Capped hold has a capital guard but no regime veto; results are not a combined portfolio. Never auto-select a winner.",
    }
