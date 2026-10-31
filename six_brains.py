"""Six transparent, rule-based research perspectives; not independent AI models."""
from math import isfinite
from statistics import mean, pstdev

NAMES = ("optimist", "skeptic", "historian", "trend_hunter", "risk_manager", "strategist")

def council(closes):
    """Returns descriptive scores in [-1, 1]; never places or recommends trades."""
    if len(closes) < 60 or any(not isfinite(p) or p <= 0 for p in closes):
        return {"status": "INSUFFICIENT_DATA", "decision": "NO_ASSESSMENT", "research_only": True}
    returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    ma20, ma50 = mean(closes[-20:]), mean(closes[-50:])
    momentum = closes[-1] / closes[-21] - 1
    volatility = pstdev(returns[-20:])
    peak = max(closes[-60:])
    drawdown = closes[-1] / peak - 1
    # Simple, explainable heuristics. Not calibrated probabilities or forecasts.
    optimist = 1.0 if momentum > 0.03 else 0.5 if momentum > 0 else -0.5
    skeptic = -1.0 if drawdown < -0.10 else -0.5 if volatility > 0.03 else 0.0
    historian = 0.5 if closes[-1] > mean(closes[-60:]) else -0.5
    trend_hunter = 1.0 if ma20 > ma50 and momentum > 0 else -1.0 if ma20 < ma50 else 0.0
    risk_manager = -1.0 if volatility > 0.04 or drawdown < -0.12 else -0.5 if volatility > 0.025 else 0.0
    strategist = 0.5 if ma20 > ma50 and closes[-1] > ma20 else -0.5
    scores = dict(zip(NAMES, (optimist, skeptic, historian, trend_hunter, risk_manager, strategist)))
    average = mean(scores.values())
    return {"status": "OK", "decision": "POSITIVE_RESEARCH" if average > 0.25 else
            "CAUTIOUS_RESEARCH" if average < -0.25 else "MIXED_RESEARCH",
            "scores": scores, "aggregate_score": round(average, 4),
            "metrics": {"momentum_20d": round(momentum, 5), "volatility_20d": round(volatility, 5),
                        "drawdown_from_60d_high": round(drawdown, 5)},
            "research_only": True}
