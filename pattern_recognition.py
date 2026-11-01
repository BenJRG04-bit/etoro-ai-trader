"""Transparent multi-signal pattern recognition for offline Project E.T. research.

Not an ML model, a probability, a trade recommendation, or an order engine.
Uses only known historical *daily closes* and fixed predeclared thresholds.
No network, account credentials or broker access.
"""
from math import isfinite
from statistics import mean, pstdev

MIN_HISTORY = 120


def _rsi14(prices):
    changes = [prices[i] - prices[i - 1] for i in range(len(prices) - 14, len(prices))]
    gain = mean(max(v, 0.0) for v in changes)
    loss = mean(max(-v, 0.0) for v in changes)
    if loss == 0:
        return 100.0 if gain > 0 else 50.0
    return 100 - 100 / (1 + gain / loss)


def analyze_price_patterns(closes):
    """Identify a research hypothesis using multiple corroborating close-only clues.

    Input is the complete price history KNOWN at signal time; never add a
    next-day price. An incomplete history returns NO_CANDIDATE rather than
    extrapolating. Invalid history raises ValueError.
    """
    safe = {"research_only": True, "orders_allowed": False,
            "demo_trading_approved": False, "live_trading_approved": False}
    if not isinstance(closes, (list, tuple)):
        raise ValueError("Expected chronological prices")
    if len(closes) < MIN_HISTORY:
        return {**safe, "status": "INSUFFICIENT_HISTORY",
                "pattern_labels": [], "risk_vetoes": ["AT_LEAST_120_CLOSES_REQUIRED"],
                "pattern_score": 0, "signal": "NO_CANDIDATE"}
    if any(type(p) not in (int, float) or not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Historical closes must be finite positive numbers")
    p = closes[-1]
    ma20 = mean(closes[-20:])
    ma50 = mean(closes[-50:])
    ma100 = mean(closes[-100:])
    previous_ma20 = mean(closes[-21:-1])
    daily = [closes[i] / closes[i - 1] - 1 for i in range(len(closes) - 60, len(closes))]
    volatility20 = pstdev(daily[-20:])
    volatility60 = pstdev(daily)
    momentum20 = p / closes[-21] - 1
    momentum5 = p / closes[-6] - 1
    last_return = p / closes[-2] - 1
    drawdown60 = p / max(closes[-60:]) - 1
    extension = p / ma20 - 1
    rsi = _rsi14(closes)

    bullish_structure = ma20 > ma50 * 1.003 and ma50 > ma100 * 1.003 and p > ma50
    bearish_structure = ma20 < ma50 * 0.997 and ma50 < ma100 * 0.997
    regime = "BULLISH_STRUCTURE" if bullish_structure else (
        "BEARISH_STRUCTURE" if bearish_structure else "UNCLEAR_STRUCTURE")

    vetoes = []
    if not bullish_structure:
        vetoes.append("NO_CONFIRMED_BULLISH_STRUCTURE")
    if volatility20 >= 0.035:
        vetoes.append("HIGH_DAILY_VOLATILITY")
    if drawdown60 <= -0.12:
        vetoes.append("DEEP_60D_DRAWDOWN")
    if last_return <= -0.06:
        vetoes.append("SHARP_LAST_DAY_DECLINE")
    if extension >= 0.10:
        vetoes.append("OVEREXTENDED_ABOVE_20D_AVERAGE")
    if rsi >= 78.0:
        vetoes.append("OVERBOUGHT_RSI")
    if momentum20 <= 0:
        vetoes.append("NEGATIVE_20D_MOMENTUM")

    breakout = p > max(closes[-21:-1]) * 1.002 and extension <= 0.08
    reclaim = (closes[-2] <= previous_ma20 and p > ma20 and p > closes[-2]
               and last_return <= 0.05)
    continuation = (momentum20 >= 0.03 and momentum5 >= 0.012
                    and 45 <= rsi < 75 and 0 <= extension <= 0.075)
    compression = volatility60 > 0.001 and volatility20 <= 0.8 * volatility60

    labels = []
    if breakout:
        labels.append("BREAKOUT_ABOVE_PRIOR_20D_HIGH")
    if reclaim:
        labels.append("PULLBACK_RECLAIMS_20D_AVERAGE")
    if continuation:
        labels.append("MOMENTUM_CONTINUATION")
    if compression:
        labels.append("VOLATILITY_COMPRESSION_CONTEXT")

    # Scores describe overlapping technical evidence, NOT model probability.
    # Volatility compression alone can NEVER trigger a candidate.
    score = (2 * int(bullish_structure) + 2 * int(breakout)
             + 2 * int(reclaim) + int(continuation) + int(compression))
    directional = breakout or reclaim or continuation
    signal = ("RESEARCH_CANDIDATE" if not vetoes and directional and score >= 4
              else "RISK_BLOCKED" if vetoes else "NO_CANDIDATE")

    return {
        **safe, "status": "OK", "signal": signal,
        "regime": regime, "pattern_labels": labels,
        "pattern_score": score, "max_pattern_score": 8,
        "evidence_strength": ("MULTIPLE_CLUES" if score >= 5 else
                              "PRELIMINARY" if score >= 4 else "WEAK_OR_MIXED"),
        "risk_vetoes": vetoes,
        "indicators": {
            "ma20": round(ma20, 6),
            "ma50": round(ma50, 6),
            "ma100": round(ma100, 6),
            "momentum5_fraction": round(momentum5, 6),
            "momentum20_fraction": round(momentum20, 6),
            "daily_volatility20": round(volatility20, 6),
            "daily_volatility60": round(volatility60, 6),
            "drawdown60_fraction": round(drawdown60, 6),
            "rsi14": round(rsi, 3),
            "distance_above_ma20_fraction": round(extension, 6),
        },
        "limitations": (
            "Fixed heuristic thresholds, correlated price-only signals; no volume, "
            "intraday bars, fundamentals, news or calibrated probability. "
            "A candidate is research-only, not evidence of future profit."
        ),
    }
