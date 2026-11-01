"""Standard-library regression tests for the event decision engine."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.market_event_engine import MarketEvent, assess

NOW = datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)

def event(**kwargs):
    data = dict(ticker="NVDA", timestamp=NOW, price=103.0,
                baseline_price=100.0, volume_ratio=2.5)
    data.update(kwargs)
    return MarketEvent(**data)

class EventEngineTests(unittest.TestCase):
    def test_unusual_event_is_review_not_trade(self):
        r = assess(event(), NOW)
        self.assertEqual(r["signal"], "REVIEW")
        self.assertEqual(r["action"], "WAIT")
        self.assertFalse(r["orders_allowed"])

    def test_stale_event_fails_closed(self):
        self.assertEqual(assess(event(timestamp=NOW-timedelta(seconds=31)), NOW)["reason"],
                         "stale_or_future_data")

    def test_future_event_fails_closed(self):
        self.assertEqual(assess(event(timestamp=NOW+timedelta(seconds=1)), NOW)["reason"],
                         "stale_or_future_data")

    def test_unknown_asset_fails_closed(self):
        self.assertEqual(assess(event(ticker="BTC"), NOW)["reason"], "unsupported_asset")

    def test_invalid_price_fails_closed(self):
        self.assertEqual(assess(event(price=float("nan")), NOW)["reason"], "invalid_numbers")

    def test_normal_event_waits(self):
        self.assertEqual(assess(event(price=100.2, volume_ratio=1), NOW)["reason"],
                         "no_unusual_event")

if __name__ == "__main__":
    unittest.main()
