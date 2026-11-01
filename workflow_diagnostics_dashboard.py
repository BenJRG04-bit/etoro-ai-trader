"""Offline, static workflow execution dashboard from actual Actions metadata."""
import html
import json
from pathlib import Path
from workflow_run_diagnostics import WORKFLOWS

def render_pipeline_dashboard(report):
    if not isinstance(report, dict) or report.get("status") not in ("WORKFLOW_RUNS_PRESENT", "WORKFLOW_VERIFICATION_INCOMPLETE"):
        raise ValueError("Invalid pipeline report")
    if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe pipeline report")
    workflows = report.get("workflows")
    blockers = report.get("blockers")
    if not isinstance(workflows, dict) or set(workflows) != set(WORKFLOWS.values()):
        raise ValueError("Missing monitored workflows")
    if not isinstance(blockers, list) or not all(isinstance(x, str) for x in blockers):
        raise ValueError("Invalid blockers")
    def escape(value):
        return html.escape(str(value), quote=True)
    rows = []
    actual_blockers = []
    for filename, label in WORKFLOWS.items():
        item = workflows[label]
        if not isinstance(item, dict) or item.get("workflow") != filename:
            raise ValueError("Invalid workflow mapping")
        status = item.get("status")
        if status not in ("SUCCESS", "NO_RUN_FOUND", "INCOMPLETE_OR_FAILED", "STALE_RUN", "FETCH_ERROR"):
            raise ValueError("Unknown workflow state")
        artifact = item.get("artifact_status")
        if artifact is not None and artifact not in ("PRESENT", "NOT_CHECKED", "MISSING_OR_EXPIRED", "FETCH_ERROR", "INVALID_RUN_ID"):
            raise ValueError("Invalid artifact status")
        if status != "SUCCESS" or (artifact is not None and artifact != "PRESENT"):
            actual_blockers.append(label)
        age = item.get("age_hours", "—")
        if type(age) not in (float, int, str) or (isinstance(age, (float, int)) and age < 0):
            raise ValueError("Invalid workflow age")
        rows.append("<tr><td>" + escape(label.replace("_", " ").title()) +
                    "</td><td>" + escape(status) + "</td><td>" + escape(age) +
                    "</td><td>" + escape(item.get("conclusion", "—")) + "</td><td>" + escape(artifact if artifact is not None else "NOT_CHECKED") + "</td></tr>")
    if blockers != actual_blockers:
        raise ValueError("Inconsistent blockers")
    if (report["status"] == "WORKFLOW_RUNS_PRESENT") != (not blockers):
        raise ValueError("Contradictory overall status")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project E.T. | Pipeline Health</title>
<style>:root{color-scheme:dark}body{background:#0f192a;color:#e7f0ff;font:16px system-ui,sans-serif;padding:24px}
main{max-width:1000px;margin:auto}section{background:#1c2b44;padding:20px;border-radius:12px;margin:20px 0}
.warning{border-left:5px solid #ffcc6d;padding:12px;background:#42331d}
table{width:100%;border-collapse:collapse}th,td{padding:12px;text-align:left;border-bottom:1px solid #42516b}
.scroll{overflow-x:auto}small{color:#c6d7ee}</style></head><body><main>
<h1>Project E.T. — Research Pipeline Health</h1>
<p class="warning"><strong>RESEARCH ONLY — NO LIVE TRADING.</strong>
A successful workflow does not prove accurate predictions or profitable strategies.</p>
<section><h2>Execution status: """ + escape(report["status"]) + """</h2>
<p>Unverified workflows: """ + escape(len(blockers)) + """ of """ + escape(len(WORKFLOWS)) + """</p></section>
<section class="scroll"><table><thead><tr><th>Workflow</th><th>Status</th><th>Age (hours)</th><th>Conclusion</th><th>Artifact</th></tr></thead>
<tbody>""" + "".join(rows) + """</tbody></table></section>
<small>Based on GitHub Actions metadata, not market outcomes. Static HTML with no scripts or external resources.</small>
</main></body></html>"""

def build_pipeline_dashboard(directory="."):
    root = Path(directory)
    with (root / "workflow_diagnostics_report.json").open(encoding="utf-8") as handle:
        report = json.load(handle)
    target = root / "workflow_diagnostics_dashboard.html"
    target.write_text(render_pipeline_dashboard(report), encoding="utf-8")
    return str(target)

if __name__ == "__main__":
    print(build_pipeline_dashboard())
