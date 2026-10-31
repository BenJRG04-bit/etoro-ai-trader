"""Build a safe, self-contained HTML dashboard from existing research JSON.

No scripts, network access, broker integration, or order placement.
All text is escaped before HTML rendering.
"""
import html
import json
from datetime import datetime, timezone
from pathlib import Path

REPORT_FILES = {
    "paper": "paper_experiment_results.json",
    "decisions": "decision_diagnostic_report.json",
    "veto_outcomes": "risk_veto_report.json",
    "severity": "risk_severity_report.json",
    "holdout": "holdout_risk_audit.json",
    "quality": "evidence_quality_report.json",
    "strategies": "strategy_evaluation_report.json",
}

def _safe(value):
    return html.escape(str(value), quote=True)

def _number(value, digits=2):
    return "N/A" if value is None else f"{float(value):.{digits}f}"

def _fraction(value):
    return "N/A" if value is None else f"{float(value) * 100:+.2f}%"

def _extract_paper(item):
    report = item.get("report", {})
    return report

def render_dashboard(reports, generated_at=None):
    if not isinstance(reports, dict):
        raise ValueError("Reports must be a mapping")
    generated_at = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    symbols = sorted(set().union(*(set(v.get("assets", {})) for v in reports.values() if isinstance(v, dict))))
    rows = []
    for ticker in symbols:
        paper = reports.get("paper", {}).get("assets", {}).get(ticker, {})
        quality = reports.get("quality", {}).get("assets", {}).get(ticker, {})
        severity = reports.get("severity", {}).get("assets", {}).get(ticker, {})
        holdout = reports.get("holdout", {}).get("assets", {}).get(ticker, {})
        evaluation = reports.get("strategies", {}).get("assets", {}).get(ticker, {})
        available = [name for name in REPORT_FILES if reports.get(name, {}).get("assets", {}).get(ticker, {}).get("status") == "EXPLORATORY_ONLY"]
        missing = sorted(set(REPORT_FILES) - set(available))
        paper_data = _extract_paper(paper) if paper.get("status") == "EXPLORATORY_ONLY" else {}
        strategy = paper_data.get("strategy", {})
        benchmark = paper_data.get("benchmark", {})
        # Exact structure of paper report may vary. Display N/A rather than guessing.
        strategy_final = strategy.get("end_equity") if isinstance(strategy, dict) else None
        benchmark_final = benchmark.get("final_equity") if isinstance(benchmark, dict) else None
        if strategy_final is None:
            strategy_final = paper_data.get("strategy_end")
        if benchmark_final is None:
            benchmark_final = paper_data.get("benchmark_end")
        veto = severity.get("severity", {}).get("horizons", {}).get("20", {}).get("veto", {})
        later = holdout.get("audit", {}).get("segments", {}).get("later_holdout", {}).get("horizons", {}).get("20", {}).get("veto", {})
        adequate = quality.get("sample_adequate") if quality.get("status") == "EXPLORATORY_ONLY" else None
        label = "ADEQUATE COUNT ONLY" if adequate is True else "INSUFFICIENT" if adequate is False else "UNKNOWN"
        later_scenarios = evaluation.get("evaluation", {}).get("segments", {}).get("later_holdout", {}).get("scenarios", {}) if evaluation.get("status") == "EXPLORATORY_ONLY" else {}
        base_fee = later_scenarios.get("0.001", {})
        stressed_fee = later_scenarios.get("0.005", {})
        def end_value(scenarios, policy):
            return scenarios.get(policy, {}).get("end_equity")
        council_end = end_value(base_fee, "council_guarded")
        hold_end = end_value(base_fee, "capped_hold")
        stressed_end = end_value(stressed_fee, "council_guarded")
        cells = [
            _safe(ticker),
            f"{len(available)}/{len(REPORT_FILES)}",
            _safe(label),
            "£" + _number(strategy_final) if strategy_final is not None else "N/A",
            "£" + _number(benchmark_final) if benchmark_final is not None else "N/A",
            _fraction(veto.get("worst_return_fraction")),
            str(later.get("observations", "N/A")),
            _safe(", ".join(missing) if missing else "none"),
            "£" + _number(council_end) if council_end is not None else "N/A",
            "£" + _number(hold_end) if hold_end is not None else "N/A",
            "£" + _number(stressed_end) if stressed_end is not None else "N/A",
        ]
        rows.append("<tr>" + "".join("<td>" + x + "</td>" for x in cells) + "</tr>")
    headers = ("Asset", "Reports", "Sample check", "Strategy £100", "Matched hold £100", "Worst 20d veto outcome", "Later 20d veto samples", "Missing reports", "Later council £100", "Later capped hold £100", "Later council higher fee £100")
    heading = "".join("<th scope='col'>" + _safe(x) + "</th>" for x in headers)
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project E.T. | Offline Research Dashboard</title>
<style>
:root{color-scheme:dark}body{font-family:system-ui,sans-serif;background:#0e1624;color:#eef4ff;margin:0;padding:2rem;line-height:1.5}
main{max-width:1250px;margin:auto}h1{font-size:2rem;margin-bottom:.3rem}.tag{color:#9ed2ff}
aside{background:#283a51;padding:1rem;border-left:4px solid #f6c56b;margin:1.5rem 0}
section{overflow-x:auto;background:#172439;border-radius:12px;padding:1rem}table{width:100%;border-collapse:collapse;min-width:1300px}
th,td{padding:.75rem;border-bottom:1px solid #3b4c62;text-align:left;vertical-align:top}
th{color:#b9d9ff}small{color:#bdcbe0}footer{margin-top:1.5rem}
</style></head><body><main><p class="tag">PROJECT E.T. / HISTORICAL RESEARCH</p>
<h1>Unified research dashboard</h1><p>Generated: """ + _safe(generated_at) + """</p>
<aside><strong>RESEARCH ONLY — NO ORDERS OR LIVE TRADING.</strong><br>
Sample adequacy is not statistical validation. Historical observations overlap and may be misleading.
£100 tests are separate per asset, not one portfolio. Prices are unadjusted and omit FX, dividends,
spread, slippage and taxes. Missing results are explicitly marked N/A.</aside>
<section><table><thead><tr>""" + heading + "</tr></thead><tbody>" + "".join(rows) + """</tbody></table></section>
<footer><small>Read-only static HTML; no JavaScript, brokerage keys, order routing, or automatic strategy changes.</small></footer>
</main></body></html>"""

def build_dashboard(directory=".", output="research_dashboard.html"):
    root = Path(directory)
    reports = {}
    for label, filename in REPORT_FILES.items():
        path = root / filename
        try:
            with path.open(encoding="utf-8") as handle:
                report = json.load(handle)
            if not isinstance(report, dict) or report.get("orders_allowed") is not False or report.get("research_only") is not True:
                raise ValueError("Unsafe or invalid research report: " + filename)
            reports[label] = report
        except FileNotFoundError:
            reports[label] = {"assets": {}}
    document = render_dashboard(reports)
    (root / output).write_text(document, encoding="utf-8")
    return str(root / output)

if __name__ == "__main__":
    print(build_dashboard())
