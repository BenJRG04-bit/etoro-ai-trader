"""Chronological split audit of risk veto outcomes; research only.

Signals are generated from past prices. Forward outcome windows are kept
entirely inside their respective train/test segment to prevent boundary leakage.
No thresholds or strategies are fitted or selected using the holdout.
"""
from math import isfinite
from regime_council import regime_aware_council

def _summary(values):
    n = len(values)
    return {
        "observations": n,
        "mean_forward_return_fraction": round(sum(values) / n, 8) if n else None,
        "worst_forward_return_fraction": round(min(values), 8) if n else None,
        "loss_5pct_or_more_count": sum(x <= -0.05 for x in values),
        "gain_5pct_or_more_count": sum(x >= 0.05 for x in values),
    }

def audit_holdout(closes, holdout_fraction=0.30, horizons=(1, 5, 20), assessment_fn=regime_aware_council):
    if not isinstance(closes, (tuple, list)) or len(closes) < 160:
        raise ValueError("Need at least 160 daily closes")
    if any(type(p) not in (int, float) or not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Invalid close")
    if not isinstance(holdout_fraction, (float, int)) or isinstance(holdout_fraction, bool) or not 0.2 <= holdout_fraction <= 0.5:
        raise ValueError("Holdout must be between 20 and 50 percent")
    if not isinstance(horizons, (tuple, list)) or not horizons or any(type(h) is not int or not 1 <= h <= 30 for h in horizons) or len(set(horizons)) != len(horizons):
        raise ValueError("Horizons must be distinct integers between 1 and 30")
    split = int(len(closes) * (1 - holdout_fraction))
    if split < 80 or len(closes) - split < max(horizons) + 10:
        raise ValueError("Not enough observations in each segment")
    results = {}
    for label, start, end in (("earlier", 59, split), ("later_holdout", split, len(closes))):
        by_horizon = {}
        for h in horizons:
            veto_returns, nonveto_returns = [], []
            for t in range(start, end - h):
                decision = assessment_fn(closes[:t + 1])
                veto = decision["regime_risk_veto"]
                if type(veto) is not bool:
                    raise ValueError("Risk veto must be boolean")
                (veto_returns if veto else nonveto_returns).append(closes[t + h] / closes[t] - 1)
            by_horizon[str(h)] = {
                "veto": _summary(veto_returns),
                "non_veto": _summary(nonveto_returns),
            }
        results[label] = {"first_signal_index": start, "last_price_index_exclusive": end, "horizons": by_horizon}
    return {
        "mode": "CHRONOLOGICAL_HOLDOUT_RESEARCH_ONLY",
        "split_price_index": split,
        "segments": results,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Later segment is a fixed chronological audit, not a truly untouched holdout if viewed or used for design. Overlapping windows are dependent; not evidence of causality or profitability. No parameter tuning, costs, dividends, FX, or execution modeling.",
    }
