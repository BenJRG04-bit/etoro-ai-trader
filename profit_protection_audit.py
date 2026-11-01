"""Offline profit-retention audit of synchronized hypothetical portfolio equity curves."""
from math import isfinite


def audit_equity_curve(curve):
    if not isinstance(curve, (list, tuple)) or len(curve) < 2:
        raise ValueError("Need at least two equity observations")
    if any(type(v) not in (int, float) or not isfinite(v) or v <= 0 for v in curve):
        raise ValueError("Invalid equity observations")
    starting = float(curve[0])
    peak = starting
    peak_index = 0
    worst = (0.0, 0, 0)
    underwater = 0
    longest_underwater = 0
    for i, equity in enumerate(curve):
        if equity >= peak:
            peak, peak_index = equity, i
            underwater = 0
        else:
            underwater += 1
            longest_underwater = max(longest_underwater, underwater)
            drawdown = (peak - equity) / peak
            if drawdown > worst[0]:
                worst = (drawdown, peak_index, i)
    maximum = max(curve)
    earned_at_peak = max(0.0, maximum - starting)
    given_back = max(0.0, maximum - curve[-1])
    return {"observations": len(curve), "starting_equity": round(starting, 4),
            "ending_equity": round(curve[-1], 4), "highest_equity": round(maximum, 4),
            "maximum_drawdown_fraction": round(worst[0], 6),
            "drawdown_peak_index": worst[1], "drawdown_trough_index": worst[2],
            "longest_underwater_observations": longest_underwater,
            "peak_profit_given_back_fraction": round(min(1.0, given_back / earned_at_peak), 6) if earned_at_peak else None,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Retrospective curve metrics; profit-giveback fraction is undefined if the curve never exceeded initial equity. Cannot guarantee protection from gaps or future losses."}
