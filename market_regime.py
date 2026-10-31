"""Research-only market regime labels. Descriptive, not predictive."""
from math import isfinite
from statistics import mean, pstdev

def classify_regime(closes):
    if len(closes) < 60 or any(not isfinite(x) or x <= 0 for x in closes):
        return {"regime": "INSUFFICIENT_DATA", "research_only": True}
    ma20 = mean(closes[-20:])
    ma50 = mean(closes[-50:])
    returns = [closes[i] / closes[i-1] - 1 for i in range(len(closes)-20, len(closes))]
    vol = pstdev(returns)
    peak = max(closes[-60:])
    drawdown = closes[-1] / peak - 1
    if vol >= 0.03 or drawdown <= -0.12:
        regime = "HIGH_RISK"
    elif ma20 > ma50 * 1.005:
        regime = "UPTREND"
    elif ma20 < ma50 * 0.995:
        regime = "DOWNTREND"
    else:
        regime = "SIDEWAYS"
    return {"regime": regime, "volatility_20d": round(vol, 6),
            "drawdown_60d": round(drawdown, 6),
            "ma20": round(ma20, 6), "ma50": round(ma50, 6),
            "research_only": True}
