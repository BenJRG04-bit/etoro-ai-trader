"""Walk-forward historical decision audit with a fixed non-overlapping evaluation schedule.

No model fitting is performed: these are chronological retrospective slices,
not independent live or prospective evidence.
"""
from math import isfinite
from portfolio_simulator import simulate_portfolio
from portfolio_benchmark import _always_eligible

SAFE = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}

def rolling_decision_audit(prices, *, starting_cash=100.0, window=90,
                           stride=30, fee_rate=.001, spread_rate=.001,
                           slippage_rate=.001, fx_rate=.005, minimum_order=1.0,
                           council_fn=None):
    if not isinstance(prices, dict) or not prices:
        raise ValueError("Missing price data")
    if type(window) is not int or window < 62 or type(stride) is not int or stride < 1:
        raise ValueError("Invalid window or stride")
    if type(starting_cash) not in (int, float) or not isfinite(starting_cash) or not 0 < starting_cash <= 100:
        raise ValueError("Invalid budget")
    lengths = {len(v) for v in prices.values()}
    if len(lengths) != 1:
        raise ValueError("Prices must be aligned")
    length = lengths.pop()
    if length < window:
        raise ValueError("Not enough data for a complete window")
    opts = {"starting_cash": starting_cash, "fee_rate": fee_rate,
            "spread_rate": spread_rate, "slippage_rate": slippage_rate,
            "fx_rate": fx_rate, "minimum_order": minimum_order}
    windows = []
    for start in range(0, length - window + 1, stride):
        segment = {ticker: values[start:start + window] for ticker, values in prices.items()}
        guarded_opts = dict(opts)
        if council_fn is not None:
            guarded_opts["assessment_fn"] = council_fn
        council = simulate_portfolio(segment, **guarded_opts)
        baseline = simulate_portfolio(segment, **{**opts, "assessment_fn": _always_eligible})
        for result in (council, baseline):
            if any(result.get(k) is not v for k, v in SAFE.items()):
                raise ValueError("Unsafe simulator result")
        windows.append({
            "start_index": start, "end_index_exclusive": start + window,
            "council_end_equity": council["end_equity"],
            "baseline_end_equity": baseline["end_equity"],
            "council_minus_baseline": round(council["end_equity"] - baseline["end_equity"], 4),
            "council_halted": council["halted"], "baseline_halted": baseline["halted"],
        })
    wins = sum(row["council_minus_baseline"] > 0 for row in windows)
    ties = sum(row["council_minus_baseline"] == 0 for row in windows)
    return {
        "status": "RETROSPECTIVE_ROLLING_AUDIT_ONLY",
        "window_days": window, "stride_days": stride,
        "windows": windows, "windows_evaluated": len(windows),
        "council_win_windows": wins, "tied_windows": ties,
        "council_win_fraction": round(wins / len(windows), 6),
        "forward_validation": "NOT_ESTABLISHED",
        "live_trading_readiness": "BLOCKED",
        **SAFE,
        "limitations": "Retrospective overlapping historical windows; results are correlated and not independent. "
                       "No training, model selection, future-data prediction, prospective performance or broker execution. "
                       "A win count is not a statistical significance test. Same costs, capital and risk caps for both policies.",
    }
