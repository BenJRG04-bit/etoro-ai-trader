"""Research-only event decision engine. Never places orders."""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

WATCHLIST = frozenset({"AAPL", "MSFT", "NVDA", "SPY", "VTI"})

@dataclass(frozen=True)
class MarketEvent:
    ticker: str
    timestamp: datetime
    price: float
    baseline_price: float
    volume_ratio: float

def assess(event: MarketEvent, now: datetime, max_age_seconds: int = 30) -> dict:
    """Fail closed on stale, malformed or unsupported inputs."""
    result = {"ticker": event.ticker, "action": "WAIT", "orders_allowed": False,
              "live_trading_approved": False, "research_only": True}
    if event.ticker not in WATCHLIST:
        return {**result, "reason": "unsupported_asset"}
    if event.timestamp.tzinfo is None or now.tzinfo is None:
        return {**result, "reason": "missing_timezone"}
    age = (now.astimezone(timezone.utc) - event.timestamp.astimezone(timezone.utc)).total_seconds()
    if age < 0 or age > max_age_seconds:
        return {**result, "reason": "stale_or_future_data"}
    values = (event.price, event.baseline_price, event.volume_ratio)
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and isfinite(v) for v in values):
        return {**result, "reason": "invalid_numbers"}
    if event.price <= 0 or event.baseline_price <= 0 or event.volume_ratio < 0:
        return {**result, "reason": "invalid_market_values"}
    change_pct = (event.price / event.baseline_price - 1) * 100
    if abs(change_pct) >= 2 and event.volume_ratio >= 2:
        return {**result, "reason": "unusual_price_and_volume",
                "signal": "REVIEW", "change_pct": round(change_pct, 3)}
    return {**result, "reason": "no_unusual_event", "change_pct": round(change_pct, 3)}
