"""Public historical daily closes for offline research; no brokerage/API keys."""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

WATCHLIST = ("AAPL", "MSFT", "NVDA", "SPY", "VTI")

def fetch_daily_closes(ticker, period="2y", opener=None):
    if ticker not in WATCHLIST:
        raise ValueError("Ticker is not in the research watchlist")
    if period not in ("1y", "2y", "5y"):
        raise ValueError("Unsupported history period")
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(ticker)
           + "?interval=1d&range=" + period)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ProjectET-Research"})
    if opener is None:
        opener = urllib.request.urlopen
    with opener(request, timeout=20) as response:
        payload = json.load(response)
    chart = payload["chart"]
    if chart.get("error"):
        raise ValueError("Market data provider returned an error")
    result = chart["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    rows = []
    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue
        price = float(close)
        if not (0 < price < float("inf")):
            continue
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
        if rows and date <= rows[-1][0]:
            raise ValueError("Non-increasing daily timestamps")
        rows.append((date, price))
    if len(rows) < 120:
        raise ValueError("Not enough valid daily prices for historical evaluation")
    return {"ticker": ticker, "source": "Yahoo Finance public chart endpoint",
            "price_type": "unadjusted_daily_close", "dates": [x[0] for x in rows],
            "closes": [x[1] for x in rows], "research_only": True}
