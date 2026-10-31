"""Scheduled, read-only market research. No orders, credentials or brokerage API."""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from project_et import WATCHLIST, analyse_prices
from six_brains import council

def fetch_closes(ticker):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + ticker + "?range=6mo&interval=1d"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ProjectETResearch/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)
    result = data["chart"]["result"][0]
    quotes = result["indicators"]["quote"][0]["close"]
    return [float(x) for x in quotes if x is not None and x > 0]

def main():
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "RESEARCH_ONLY_NO_ORDERS", "results": []}
    failures = 0
    for ticker in WATCHLIST:
        try:
            prices = fetch_closes(ticker)
            result = analyse_prices(ticker, prices)
            result["six_brain_research"] = council(prices)
            report["results"].append(result)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            failures += 1
            report["results"].append({"ticker": ticker, "signal": "DATA_ERROR",
                                      "error": type(exc).__name__, "research_only": True})
    Path("research_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        print(f"Market data unavailable for {failures} asset(s). No orders attempted.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
