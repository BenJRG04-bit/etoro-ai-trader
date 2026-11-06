"""Offline market regime classification. No broker access or orders."""
from math import isfinite

def classify_regime(closes, short_window=20, long_window=60, flat_band=0.01):
    if not isinstance(short_window, int) or not isinstance(long_window, int):
        raise ValueError("Window sizes must be integers")
    if short_window < 2 or long_window <= short_window:
        raise ValueError("Require 2 <= short_window < long_window")
    if not 0 <= flat_band < 1:
        raise ValueError("flat_band must be between 0 and 1")
    if len(closes) < long_window:
        return {"regime": "UNKNOWN", "reason": "insufficient_history", "research_only": True}
    prices = closes[-long_window:]
    if any(not isinstance(p, (int, float)) or not isfinite(p) or p <= 0 for p in prices):
        raise ValueError("Prices must be positive finite numbers")
    short_ma = sum(prices[-short_window:]) / short_window
    long_ma = sum(prices) / long_window
    gap = short_ma / long_ma - 1
    regime = "UPTREND" if gap > flat_band else "DOWNTREND" if gap < -flat_band else "SIDEWAYS"
    return {"regime": regime, "ma_gap_fraction": round(gap, 8), "research_only": True}
