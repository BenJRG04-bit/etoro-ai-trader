"""Chronological offline evaluation of fixed pattern-confluence hypotheses.

Every decision uses closes ending at t-1, then takes the price return t->t+1.
This deliberate full-bar delay avoids assuming a signal can fill at the same
closing price used to calculate it. Still no realistic broker fills.
No orders, price downloads, key access or automatic model fitting.
"""
from math import isfinite
from statistics import mean

from capital_guard import CapitalGuard
from market_regime import classify_regime
from pattern_recognition import analyze_price_patterns
from regime_council import regime_aware_council

POLICIES = ("pattern_confluence", "council_guarded", "simple_uptrend", "capped_hold")
MIN_T = 120


def _positive_policy(history, name):
    if name == "capped_hold":
        return True
    if name == "pattern_confluence":
        return analyze_price_patterns(history)["signal"] == "RESEARCH_CANDIDATE"
    if name == "council_guarded":
        result = regime_aware_council(history)
        return (result.get("status") == "OK" and
                result.get("decision") == "POSITIVE_RESEARCH" and
                result.get("regime_risk_veto") is False)
    if name == "simple_uptrend":
        return classify_regime(history)["regime"] == "UPTREND"
    raise ValueError("Unknown predefined research policy")


def _simulate_period(closes, start, stop, policy, fee_rate, slippage_rate,
                     *, starting_cash=100.0, exposure_cap=0.05):
    """Score returns for t in [start, stop), with t+1 available."""
    equity, peak = float(starting_cash), float(starting_cash)
    allocation = 0.0
    switches, invested_days, max_drawdown = 0, 0, 0.0
    guard = CapitalGuard(equity)
    for t in range(start, stop):
        # Last known input is close[t-1]. Never inspect close[t] for a signal.
        signal = _positive_policy(closes[:t], policy)
        state = guard.observe(equity)
        desired = exposure_cap if signal and not state["halted"] else 0.0
        turnover = abs(desired - allocation)
        if turnover:
            # Both a simplified commission AND a separate slippage stress
            # factor charged on notional turnover, not on whole cash.
            equity *= (1 - turnover * (fee_rate + slippage_rate))
            switches += 1
        allocation = desired
        if allocation > 0:
            invested_days += 1
        equity *= 1 + allocation * (closes[t + 1] / closes[t] - 1)
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, 1 - equity / peak)
        guard.observe(equity)
    return {
        "end_equity": round(equity, 4),
        "return_fraction": round(equity / starting_cash - 1, 6),
        "max_drawdown_fraction": round(max_drawdown, 6),
        "rebalance_events": switches,
        "invested_return_periods": invested_days,
        "capital_guard_halted": guard.halted,
        "orders_allowed": False,
    }


def evaluate_pattern_strategies(closes, *, holdout_fraction=0.30,
                                fee_rates=(0.001, 0.005),
                                slippage_rate=0.001):
    if not isinstance(closes, (list, tuple)) or len(closes) < 250:
        raise ValueError("At least 250 chronological closes required")
    if any(type(p) not in (float, int) or not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Invalid price data")
    if type(holdout_fraction) not in (float, int) or not 0.2 <= holdout_fraction <= 0.4:
        raise ValueError("Invalid holdout proportion")
    if not isinstance(fee_rates, (list, tuple)) or not fee_rates or (
        any(type(v) not in (int, float) or not isfinite(v) or not 0 <= v < 0.1
            for v in fee_rates)
    ):
        raise ValueError("Invalid fee scenarios")
    if type(slippage_rate) not in (float, int) or not isfinite(slippage_rate) or not 0 <= slippage_rate < 0.05:
        raise ValueError("Invalid slippage scenario")
    split = int(len(closes) * (1 - holdout_fraction))
    if split - MIN_T < 40 or len(closes) - split < 60:
        raise ValueError("Not enough data for both segments")

    segments = {}
    for label, start, stop in (
        ("earlier", MIN_T, split),
        ("later_holdout", split, len(closes) - 1),
    ):
        scenarios = {}
        for fee in fee_rates:
            policies = {
                name: _simulate_period(closes, start, stop, name, fee, slippage_rate)
                for name in POLICIES
            }
            candidate = policies["pattern_confluence"]["end_equity"]
            reference = policies["capped_hold"]["end_equity"]
            scenarios[str(fee)] = {
                "policies": policies,
                "pattern_minus_capped_hold": round(candidate - reference, 4),
                "pattern_beat_capped_hold": candidate > reference,
            }
        segments[label] = {
            "scored_return_periods": stop - start,
            "signal_information_last_index_is_t_minus_one": True,
            "scenarios": scenarios,
        }
    return {
        "mode": "OFFLINE_FIXED_PATTERN_RESEARCH_NO_ORDERS",
        "split_price_index": split,
        "policies": list(POLICIES),
        "segments": segments,
        "starting_cash_notional": 100.0,
        "max_allocation": 0.05,
        "slippage_rate": slippage_rate,
        "research_only": True, "orders_allowed": False,
        "demo_trading_approved": False, "live_trading_approved": False,
        "strategy_selection_automated": False,
        "limitations": (
            "Fixed close-only rule hypotheses; no tuning on later segment. "
            "Later data has already been examined in the project, so it is not "
            "an untouched independent holdout. Signal lagged one close. "
            "Costs modelled as flat fee plus notional slippage, not actual "
            "bid/ask spread or fills. No dividends, FX, splits, taxes or "
            "combined portfolio exposure. Exit fees on terminal open "
            "positions are omitted. No evidence of forward profitability."
        ),
    }
