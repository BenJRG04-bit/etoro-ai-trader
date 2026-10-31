"""Measure next-day outcomes following historical safety vetoes.

Descriptive research only. Does not modify strategy or risk controls.
"""
from math import isfinite
from regime_council import regime_aware_council

def evaluate_risk_vetoes(closes):
    if not isinstance(closes, (list, tuple)) or len(closes) < 62:
        raise ValueError("At least 62 daily closes required")
    if any(not isinstance(p, (int, float)) or not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Invalid daily close")
    veto_returns, other_returns = [], []
    for t in range(59, len(closes) - 1):
        assessment = regime_aware_council(closes[:t + 1])
        next_return = closes[t + 1] / closes[t] - 1
        (veto_returns if assessment["regime_risk_veto"] else other_returns).append(next_return)

    def summarize(values):
        return {
            "days": len(values),
            "up_days": sum(v > 0 for v in values),
            "down_days": sum(v < 0 for v in values),
            "average_next_day_return_fraction": round(sum(values) / len(values), 6) if values else None,
        }
    return {
        "mode": "OFFLINE_RISK_VETO_OUTCOME_ANALYSIS",
        "veto_days": summarize(veto_returns),
        "other_days": summarize(other_returns),
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Hindsight conditional association, not proof that veto caused or avoided a loss. One-day outcomes ignore costs, tail risk, and longer horizons. Do not tune thresholds on the same evaluation period.",
    }
