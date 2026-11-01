"""Static read-only six-brain accountability dashboard.

No scripts, external resources, broker access, or order placement.
"""
import html
import json
from pathlib import Path
from six_brains import NAMES

def escape(value):
    return html.escape(str(value), quote=True)

def render_council_dashboard(report):
    if not isinstance(report, dict) or report.get("status") != "RESEARCH_ACCOUNTABILITY_ONLY":
        raise ValueError("Invalid accountability report")
    if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe accountability report")
    assets = report.get("assets")
    if not isinstance(assets, dict):
        raise ValueError("Missing assets")
    rows = []
    details = []
    for ticker, item in sorted(assets.items()):
        if not isinstance(item, dict):
            raise ValueError("Malformed asset")
        if item.get("status") != "OBSERVED_RESEARCH":
            rows.append("<tr><td>" + escape(ticker) + "</td><td>UNAVAILABLE</td><td colspan='5'>No verified assessment</td></tr>")
            continue
        explanation = item.get("explanation")
        if not isinstance(explanation, dict) or explanation.get("status") != "RESEARCH_EXPLANATION" or explanation.get("orders_allowed") is not False:
            raise ValueError("Unsafe or incomplete explanation")
        perspectives = explanation.get("perspectives")
        if not isinstance(perspectives, dict) or set(perspectives) != set(NAMES):
            raise ValueError("Incomplete perspective data")
        agreement = explanation.get("agreement", {})
        if sum(agreement.get(k, 0) for k in ("positive", "negative", "neutral")) != 6:
            raise ValueError("Invalid agreement counts")
        cells = (ticker, item.get("as_of", "N/A"), explanation.get("market_regime", "N/A"),
                 explanation.get("original_decision", "N/A"), explanation.get("confirmed_decision", "N/A"),
                 "YES" if explanation.get("risk_veto") is True else "NO",
                 "/".join(str(agreement[k]) for k in ("positive", "negative", "neutral")))
        rows.append("<tr>" + "".join("<td>" + escape(cell) + "</td>" for cell in cells) + "</tr>")
        score_rows = []
        for name in NAMES:
            value = perspectives[name]
            if not isinstance(value, dict):
                raise ValueError("Invalid perspective")
            score_rows.append("<tr><td>" + escape(name) + "</td><td>" +
                              escape(value.get("score", "N/A")) + "</td><td>" +
                              escape(value.get("stance", "N/A")) + "</td></tr>")
        reasons = "".join("<li>" + escape(reason) + "</li>" for reason in explanation.get("reasons", []))
        details.append("<section><h2>" + escape(ticker) + " — perspective breakdown</h2>" +
                       "<table><thead><tr><th>Perspective</th><th>Score</th><th>Stance</th></tr></thead><tbody>" +
                       "".join(score_rows) + "</tbody></table><h3>Decision notes</h3><ul>" + reasons + "</ul></section>")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project E.T. | Six-Brain Accountability</title>
<style>:root{color-scheme:dark}body{background:#101928;color:#edf4ff;font:16px system-ui,sans-serif;margin:0;padding:24px;line-height:1.5}
main{max-width:1150px;margin:auto}.warning{background:#40311f;border-left:5px solid #f8c76c;padding:16px}
section{background:#1b2a42;border-radius:12px;padding:18px;margin:20px 0;overflow-x:auto}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #40516b;padding:10px;text-align:left}
th{color:#a9d3ff}small{color:#c5d5ed}</style></head><body><main>
<h1>Project E.T. — Six-Brain Accountability</h1>
<div class="warning"><strong>RESEARCH ONLY — NO ORDERS OR LIVE TRADING.</strong>
<p>These are six deterministic heuristic perspectives, not independent AI models.
Scores are not calibrated confidence or forecasts; explanations are descriptive.</p></div>
<section><h2>Latest available assessments</h2><table><thead><tr>
<th>Asset</th><th>As of</th><th>Regime</th><th>Original</th><th>Confirmed</th>
<th>Risk veto</th><th>Positive / Negative / Neutral</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></section>""" + "".join(details) + """
<footer><small>Offline static HTML. No JavaScript, external assets, credentials, or trade execution.</small></footer>
</main></body></html>"""

def build_council_dashboard(directory=".", output="council_accountability_dashboard.html"):
    root = Path(directory)
    with (root / "council_accountability_report.json").open(encoding="utf-8") as handle:
        report = json.load(handle)
    page = render_council_dashboard(report)
    (root / output).write_text(page, encoding="utf-8")
    return str(root / output)

if __name__ == "__main__":
    print(build_council_dashboard())
