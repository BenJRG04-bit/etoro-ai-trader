"""Offline end-to-end readiness dashboard. No network, scripts or brokerage access."""
import html
import json
from pathlib import Path

def e(value):
    return html.escape(str(value), quote=True)

def render_readiness_dashboard(report):
    if not isinstance(report, dict) or report.get("status") not in ("RESEARCH_COVERAGE_READY", "MORE_EVIDENCE_REQUIRED"):
        raise ValueError("Invalid readiness report")
    if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe readiness report")
    issues = report.get("issues")
    if not isinstance(issues, list) or any(not isinstance(item, str) for item in issues):
        raise ValueError("Invalid readiness issues")
    if report["status"] == "RESEARCH_COVERAGE_READY" and issues:
        raise ValueError("Contradictory readiness status")
    if report["status"] == "MORE_EVIDENCE_REQUIRED" and not issues:
        raise ValueError("Missing readiness reasons")
    checks = report.get("checks", {})
    if not isinstance(checks, dict):
        raise ValueError("Invalid readiness checks")
    cards = []
    for name in ("history", "forward"):
        source = checks.get(name)
        if source is None:
            cards.append("<section><h2>" + e(name.title()) + "</h2><p>Report unavailable — no verified evidence.</p></section>")
            continue
        if not isinstance(source, dict) or source.get("status") not in ("COVERAGE_OK", "NEEDS_MORE_EVIDENCE"):
            raise ValueError("Invalid component status")
        if source.get("research_only") is not True or source.get("orders_allowed") is not False or source.get("live_trading_approved") is not False:
            raise ValueError("Unsafe component report")
        if report["status"] == "RESEARCH_COVERAGE_READY" and source["status"] != "COVERAGE_OK":
            raise ValueError("Contradictory component coverage")
        details = []
        for key in ("dates", "observed_snapshots", "total_snapshots", "pending_snapshots", "unavailable_snapshots"):
            if key in source:
                details.append("<li>" + e(key.replace("_", " ")) + ": " + e(source[key]) + "</li>")
        component_issues = source.get("issues", [])
        if not isinstance(component_issues, list):
            raise ValueError("Invalid component issues")
        cards.append("<section><h2>" + e(name.title()) + "</h2><p>Status: <strong>" +
                     e(source["status"]) + "</strong></p><ul>" + "".join(details) +
                     "".join("<li>" + e(x) + "</li>" for x in component_issues) + "</ul></section>")
    if report["status"] == "RESEARCH_COVERAGE_READY" and set(checks) != {"history", "forward"}:
        raise ValueError("Incomplete coverage checks")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project E.T. | Research Readiness</title>
<style>:root{color-scheme:dark}body{background:#101928;color:#edf4ff;font:16px system-ui,sans-serif;padding:24px;line-height:1.5}
main{max-width:960px;margin:auto}.warning{background:#40311f;border-left:5px solid #f8c76c;padding:16px}
section{background:#1b2a42;border-radius:12px;padding:18px;margin:20px 0}
small{color:#c5d5ed}</style></head><body><main>
<h1>Project E.T. — Research Readiness</h1><div class="warning">
<strong>DEMO RESEARCH ONLY — NO ORDERS OR LIVE TRADING.</strong>
<p>Data coverage is not predictive skill, financial performance, or approval to invest.</p></div>
<section><h2>Combined status: """ + e(report["status"]) + """</h2>
<p>Reasons:</p><ul>""" + ("".join("<li>" + e(x) + "</li>" for x in issues) if issues else "<li>No coverage blockers reported</li>") + """</ul></section>""" + "".join(cards) + """
<footer><small>Static HTML. No JavaScript, external assets or trading functionality.</small></footer>
</main></body></html>"""

def build_readiness_dashboard(directory=".", output="research_readiness_dashboard.html"):
    root = Path(directory)
    with (root / "research_readiness_report.json").open(encoding="utf-8") as f:
        report = json.load(f)
    page = render_readiness_dashboard(report)
    destination = root / output
    destination.write_text(page, encoding="utf-8")
    return str(destination)

if __name__ == "__main__":
    print(build_readiness_dashboard())
