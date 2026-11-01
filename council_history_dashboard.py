"""Render a self-contained, read-only dashboard of archived council decisions."""
import html
import json
from pathlib import Path
from historical_prices import WATCHLIST

def esc(value):
    return html.escape(str(value), quote=True)

def render_council_history_dashboard(report):
    if not isinstance(report, dict) or report.get("status") != "RESEARCH_ACCOUNTABILITY_HISTORY":
        raise ValueError("Invalid history report")
    if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe history report")
    assets, timeline = report.get("assets"), report.get("timeline")
    if not isinstance(assets, dict) or set(assets) != set(WATCHLIST) or not isinstance(timeline, list):
        raise ValueError("Invalid history data")
    if report.get("selected_report_dates") != len(timeline):
        raise ValueError("Timeline count mismatch")
    rows = []
    for ticker in sorted(WATCHLIST):
        item = assets[ticker]
        if not isinstance(item, dict):
            raise ValueError("Invalid asset summary")
        keys = ("observations", "original_positive", "confirmed_positive",
                "risk_veto", "mixed_perspectives", "awaiting_confirmation")
        if any(type(item.get(key)) is not int or item[key] < 0 for key in keys):
            raise ValueError("Invalid summary count")
        if any(item[key] > item["observations"] for key in keys[1:]):
            raise ValueError("Impossible summary count")
        rows.append("<tr>" + "".join("<td>" + esc(value) + "</td>" for value in
            (ticker,) + tuple(item[key] for key in keys)) + "</tr>")
    day_rows = []
    previous = ""
    for day in timeline:
        if not isinstance(day, dict) or not isinstance(day.get("date"), str) or day["date"] <= previous:
            raise ValueError("Unsorted timeline")
        previous = day["date"]
        per_asset = day.get("assets")
        if not isinstance(per_asset, dict) or set(per_asset) != set(WATCHLIST):
            raise ValueError("Missing daily assets")
        for ticker in sorted(WATCHLIST):
            entry = per_asset[ticker]
            if not isinstance(entry, dict):
                raise ValueError("Invalid daily entry")
            if entry.get("status") == "UNAVAILABLE":
                decision, confirmed, veto = "UNAVAILABLE", "—", "—"
            elif entry.get("status") == "OBSERVED_RESEARCH":
                decision, confirmed = entry.get("original", ""), entry.get("confirmed", "")
                veto = "YES" if entry.get("risk_veto") is True else "NO"
            else:
                raise ValueError("Unknown daily status")
            day_rows.append("<tr>" + "".join("<td>" + esc(v) + "</td>" for v in
                (day["date"], ticker, decision, confirmed, veto)) + "</tr>")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project E.T. | Decision History</title>
<style>:root{color-scheme:dark}body{background:#101928;color:#edf4ff;font:16px system-ui,sans-serif;padding:24px;line-height:1.5}
main{max-width:1150px;margin:auto}.warning{background:#40311f;border-left:5px solid #f8c76c;padding:16px}
section{background:#1b2a42;border-radius:12px;padding:18px;margin:20px 0;overflow-x:auto}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #40516b;padding:10px;text-align:left}
th{color:#a9d3ff}small{color:#c5d5ed}</style></head><body><main>
<h1>Project E.T. — Archived Decision History</h1>
<div class="warning"><strong>RESEARCH ONLY — NO LIVE TRADING OR ORDERS.</strong>
<p>Counts past heuristic decisions, not trading returns, prediction accuracy or evidence of profit.</p></div>
<section><h2>Coverage</h2><p>Archived report dates: """ + esc(report["selected_report_dates"]) + """
 | Rejected reports: """ + esc(report.get("rejected_reports", 0)) + """
 | First: """ + esc(report.get("first_date") or "None") + """
 | Last: """ + esc(report.get("last_date") or "None") + """</p></section>
<section><h2>Decision frequencies by asset</h2>
<table><thead><tr><th>Asset</th><th>Observations</th><th>Original positive</th>
<th>Confirmed positive</th><th>Risk veto</th><th>Disagreements</th><th>Waiting confirmation</th>
</tr></thead><tbody>""" + "".join(rows) + """</tbody></table></section>
<section><h2>Chronological decision log</h2><table><thead><tr><th>Date</th><th>Asset</th>
<th>Original</th><th>Confirmed</th><th>Risk veto</th></tr></thead><tbody>""" +
        "".join(day_rows) + """</tbody></table></section>
<footer><small>Offline HTML, no JavaScript, no external assets, no brokerage access.</small></footer>
</main></body></html>"""

def build_council_history_dashboard(directory=".", output="council_history_dashboard.html"):
    root = Path(directory)
    with (root / "council_history_report.json").open(encoding="utf-8") as f:
        report = json.load(f)
    html_page = render_council_history_dashboard(report)
    destination = root / output
    destination.write_text(html_page, encoding="utf-8")
    return str(destination)

if __name__ == "__main__":
    print(build_council_history_dashboard())
