import io
import json
import unittest
from unittest.mock import patch
from historical_prices import fetch_daily_closes, WATCHLIST
from historical_report import build_historical_report

class FakeResponse:
    def __init__(self, data):
        self.stream = io.BytesIO(json.dumps(data).encode())
    def __enter__(self):
        return self.stream
    def __exit__(self, *args):
        self.stream.close()

class HistoricalPricesTests(unittest.TestCase):
    def test_all_tickers(self):
        self.assertEqual(set(WATCHLIST), {"AAPL", "MSFT", "NVDA", "SPY", "VTI"})

    def test_bad_ticker_rejected_without_network(self):
        with self.assertRaises(ValueError):
            fetch_daily_closes("UNKNOWN")

    def test_parse_mock_daily_closes(self):
        data = {"chart": {"error": None, "result": [{
            "timestamp": [1600000000 + i * 86400 for i in range(130)],
            "indicators": {"quote": [{"close": [100.0 + i for i in range(130)]}]}
        }]}}
        r = fetch_daily_closes("AAPL", opener=lambda request, timeout: FakeResponse(data))
        self.assertEqual(len(r["closes"]), 130)
        self.assertEqual(r["closes"][0], 100.0)

    def test_report_data_failure_is_explicit(self):
        with patch("historical_report.fetch_daily_closes", side_effect=OSError("offline")):
            report = build_historical_report()
        self.assertTrue(report["research_only"])
        self.assertTrue(all(v["status"] == "DATA_OR_EVALUATION_ERROR"
                            for v in report["assets"].values()))

if __name__ == "__main__":
    unittest.main()
