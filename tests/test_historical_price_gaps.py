"""Reject missing prices rather than silently bridging an unknown market interval."""
import io
import json
import unittest
from historical_prices import fetch_daily_closes


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return io.BytesIO(json.dumps(self.payload).encode("utf-8"))

    def __exit__(self, *args):
        return False


def payload(closes):
    return {"chart": {"error": None, "result": [{
        "timestamp": [1600000000 + i * 86400 for i in range(130)],
        "indicators": {"quote": [{"close": closes}]},
    }]}}


class HistoricalPriceGapTests(unittest.TestCase):
    def test_missing_close_is_rejected(self):
        prices = [100.0 + i for i in range(130)]
        prices[40] = None
        with self.assertRaisesRegex(ValueError, "Missing daily close"):
            fetch_daily_closes("SPY", opener=lambda *args, **kwargs:
                               Response(payload(prices)))

    def test_mismatched_counts_rejected(self):
        with self.assertRaisesRegex(ValueError, "counts differ"):
            fetch_daily_closes("SPY", opener=lambda *args, **kwargs:
                               Response(payload([100.0] * 129)))

    def test_complete_series_accepted(self):
        result = fetch_daily_closes(
            "SPY", opener=lambda *args, **kwargs:
            Response(payload([100.0 + i for i in range(130)])))
        self.assertEqual(len(result["closes"]), 130)


if __name__ == "__main__":
    unittest.main()
