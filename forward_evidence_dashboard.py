"""Static, offline HTML overview of archived forward research.

No JavaScript, external assets, broker access or order placement.
"""
import html
import json
from pathlib import Path

def esc(value):
    return html.escape(str(value), quote=True)

def render_forward_dashboard(audit, quality):
    if not isinstance(audit, dict) or not isinstance(quality, dict):
        raise ValueError("Expected research JSON objects")
    if audit.get("status") != "RESEARCH_AUDIT" or quality.get("status") != "RESEARCH_EVIDENCE_ONLY":
        raise ValueError("Reports not available")
    if audit.get("orders_allowed") is not False or quality.get("orders_allowed") is not False:
        raise ValueError("Unsafe research report")
    metrics = ("snapshot_count", "observed_snapshots", "pending_snapshots",
               "unavailable_snapshots", "rejected_snapshots")
    cards = "".join("<div class='card'><strong>" + esc(audit.get(k, "N/A")) +
                    "</strong><span>" + esc(k.replace("_", " ").title()) + "</span></div>"
                    for k in metrics)
    rows = []
    for policy, assets in sorted(quality.get("policies", {}).items()):
        for ticker, item in sorted(assets.items()):
            status = "COUNT THRESHOLD MET (NOT VALIDATED)" if item.get("minimum_evidence_met") else "INSUFFICIENT SAMPLE"
            cells = (policy, ticker, item.get("signals", 0), item.get("up", 0),
                     item.get("down", 0), item.get("flat", 0),
                     item.get("distinct_signal_dates", 0), status)
            rows.append("<tr>" + "".join("<td>" + esc(c) + "</td>" for c in cells) + "</tr>")
    recent = []
    for item in sorted(audit.get("results", []), key=lambda x: x.get("snapshot_date", ""), reverse=True)[:15]:
        recent.append("<tr>" + "".join("<td>" + esc(item.get(k, "N/A")) + "</td>"
                      for k in ("snapshot_date", "status", "observed_assets", "pending_assets")) + "</tr>")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project E.T. | Forward Evidence Dashboard</title>
<style>:root{color-scheme:dark}body{background:#101928;color:#eaf2ff;font:16px system-ui,sans-serif;margin:0;padding:24px}
main{max-width:1150px;margin:auto}h1{font-size:2rem}.warning{background:#3d3020;border-left:5px solid #f8c76c;padding:16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:24px 0}
.card,section{background:#1b2a42;border-radius:12px;padding:16px}.card strong{display:block;font-size:2rem}
.card span{color:#c5d5ed}section{overflow-x:auto;margin:18px 0}table{border-collapse:collapse;width:100%}
th,td{padding:10px;border-bottom:1px solid #40516b;text-align:left;white-space:nowrap}
th{color:#a9d3ff}small{color:#c5d5ed}</style></head><body><main>
<h1>Project E.T. — Forward Evidence</h1>
<div class="warning"><strong>RESEARCH ONLY — NO ORDERS OR LIVE TRADING.</strong>
<p>Directional next-close observations are not trade returns or proof of profitability.
Signals may be correlated. Counts do not establish statistical significance.
Missing, expired, or unavailable snapshots reduce coverage.</p></div>
<div class="cards">""" + cards + """</div>
<section><h2>Recorded positive-signal outcomes</h2>
<table><thead><tr><th>Policy</th><th>Asset</th><th>Signals</th><th>Up</th><th>Down</th><th>Flat</th><th>Distinct dates</th><th>Evidence label</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table>
<p><small>Empty table means no observed positive signals yet. Sample thresholds are descriptive only.</small></p></section>
<section><h2>Most recent archived snapshots</h2>
<table><thead><tr><th>Date</th><th>Status</th><th>Observed assets</th><th>Pending assets</th></tr></thead><tbody>""" + "".join(recent) + """</tbody></table></section>
<footer><small>Offline static HTML. No scripts, tracking, broker credentials, or order execution.</small></footer>
</main></body></html>"""

def build_forward_dashboard(directory=".", output="forward_evidence_dashboard.html"):
    root = Path(directory)
    with (root / "forward_batch_audit_report.json").open(encoding="utf-8") as f:
        audit = json.load(f)
    with (root / "forward_evidence_quality_report.json").open(encoding="utf-8") as f:
        quality = json.load(f)
    page = render_forward_dashboard(audit, quality)
    (root / output).write_text(page, encoding="utf-8")
    return str(root / output)

if __name__ == "__main__":
    print(build_forward_dashboard())
