"""Project E.T. offline research engine. No brokerage access or order execution."""
from dataclasses import dataclass
from statistics import mean

WATCHLIST = ("AAPL", "MSFT", "NVDA", "SPY", "VTI")

@dataclass(frozen=True)
class RiskPolicy:
    max_position_fraction: float = 0.05
    max_experimental_fraction: float = 0.10
    max_drawdown_fraction: float = 0.10
    min_history: int = 60

def analyse_prices(ticker, closes, policy=RiskPolicy()):
    if ticker not in WATCHLIST:
        raise ValueError("Unknown watchlist ticker")
    if len(closes) < policy.min_history or any(p <= 0 for p in closes):
        return {"ticker": ticker, "signal": "NO_DATA", "research_only": True}
    fast, slow = mean(closes[-20:]), mean(closes[-50:])
    signal = "UPTREND" if fast > slow else "DOWNTREND" if fast < slow else "FLAT"
    return {"ticker": ticker, "signal": signal, "ma20": round(fast, 4),
            "ma50": round(slow, 4), "research_only": True}

def risk_gate(peak_equity, current_equity, position_fraction, experimental_fraction,
              policy=RiskPolicy()):
    if peak_equity <= 0 or current_equity < 0:
        return False, "Invalid equity"
    if not (0 <= position_fraction <= 1 and 0 <= experimental_fraction <= 1):
        return False, "Invalid allocation"
    if (peak_equity - current_equity) / peak_equity >= policy.max_drawdown_fraction:
        return False, "Drawdown limit"
    if position_fraction > policy.max_position_fraction:
        return False, "Position limit"
    if experimental_fraction > policy.max_experimental_fraction:
        return False, "Experimental limit"
    return True, "Within research limits"

if __name__ == "__main__":
    print("Project E.T. | OFFLINE RESEARCH ONLY | NO ORDERS")
    print("Watchlist:", ", ".join(WATCHLIST))
