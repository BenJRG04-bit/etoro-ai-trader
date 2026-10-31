"""Offline diagnostics for shared-portfolio council decisions.

Diagnostic signals use historical data available through the decision close.
The subsequent price move is labelled only after the decision for analysis.
No optimization, order execution or live-trading authorization.
"""
from math import isfinite
from regime_council import regime_aware_council

def diagnose_portfolio_decisions(price_series, *, fee_rate=0.001,
                                 max_total_allocation=0.05,
                                 assessment_fn=regime_aware_council):
    if not isinstance(price_series, dict) or not price_series:
        raise ValueError("Need nonempty aligned price series")
    if type(fee_rate) not in (float, int) or not isfinite(fee_rate) or not 0 <= fee_rate < 1:
        raise ValueError("Invalid fee rate")
    if type(max_total_allocation) not in (float, int) or not isfinite(max_total_allocation) or not 0 <= max_total_allocation <= 0.05:
        raise ValueError("Invalid total allocation")
    symbols = sorted(price_series)
    n = len(price_series[symbols[0]])
    if n < 62:
        raise ValueError("Insufficient aligned prices")
    for ticker in symbols:
        closes = price_series[ticker]
        if not isinstance(ticker, str) or not ticker or not isinstance(closes, (tuple, list)) or len(closes) != n:
            raise ValueError("Invalid ticker or length")
        if any(type(v) not in (float, int) or not isfinite(v) or v <= 0 for v in closes):
            raise ValueError("Invalid close")
    counts = {ticker: {"positive_days": 0, "veto_days": 0, "nonpositive_days": 0,
                       "nonpositive_before_up_day": 0, "veto_before_down_day": 0}
              for ticker in symbols}
    allocations = {ticker: 0.0 for ticker in symbols}
    switches = 0
    estimated_fee_fraction_of_start = 0.0
    days_any_eligible = 0
    days_all_in_cash = 0
    max_total_exposure = 0.0
    for t in range(59, n - 1):
        eligible = []
        for ticker in symbols:
            decision = assessment_fn(price_series[ticker][:t + 1])
            if not isinstance(decision, dict):
                raise ValueError("Invalid assessment")
            veto = bool(decision.get("regime_risk_veto", False))
            positive = decision.get("status") == "OK" and decision.get("decision") == "POSITIVE_RESEARCH" and not veto
            next_return = price_series[ticker][t + 1] / price_series[ticker][t] - 1
            row = counts[ticker]
            if veto:
                row["veto_days"] += 1
                if next_return < 0:
                    row["veto_before_down_day"] += 1
            if positive:
                eligible.append(ticker)
                row["positive_days"] += 1
            else:
                row["nonpositive_days"] += 1
                if next_return > 0:
                    row["nonpositive_before_up_day"] += 1
        target = max_total_allocation / len(eligible) if eligible else 0.0
        desired = {ticker: target if ticker in eligible else 0.0 for ticker in symbols}
        turnover = sum(abs(desired[ticker] - allocations[ticker]) for ticker in symbols)
        if turnover > 1e-12:
            switches += 1
        estimated_fee_fraction_of_start += turnover * fee_rate
        allocations = desired
        max_total_exposure = max(max_total_exposure, sum(desired.values()))
        if eligible:
            days_any_eligible += 1
        else:
            days_all_in_cash += 1
    return {
        "observed_decision_days": n - 60,
        "days_any_eligible": days_any_eligible,
        "days_all_in_cash": days_all_in_cash,
        "portfolio_target_changes": switches,
        "sum_absolute_weight_changes": round(estimated_fee_fraction_of_start / fee_rate, 6) if fee_rate else None,
        "approx_fee_fraction_of_starting_capital": round(estimated_fee_fraction_of_start, 8),
        "max_total_target_exposure": round(max_total_exposure, 6),
        "assets": counts,
        "research_only": True, "orders_allowed": False, "live_trading_approved": False,
        "limitations": "Descriptive hindsight; up-days missed do not prove a profitable trade was available. Fee approximation sums weight changes at constant starting equity, excludes compounding, execution, spread, slippage, FX and dividends. Does not model capital-guard halts; counts are not realized trades.",
    }
