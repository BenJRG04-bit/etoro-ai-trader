"""Offline, single-file command centre for safe research artifacts."""
import html
import json
from pathlib import Path

FLAGS = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}


def build_command_centre(reports):
    if not isinstance(reports, dict):
        raise ValueError("Reports must be a mapping")
    cards = []
    for name in ("central_research", "small_budget", "execution_costs", "cost_adjusted", "decision_quality", "forward_attribution", "unified_evidence"):
        report = reports.get(name)
        if report is None:
            cards.append((name, "NOT_AVAILABLE", "No report provided"))
            continue
        if not isinstance(report, dict) or any(report.get(k) is not v for k, v in FLAGS.items()):
            cards.append((name, "BLOCKED_UNSAFE_REPORT", "Invalid safety flags"))
            continue
        status = report.get("status")
        if not isinstance(status, str) or not status:
            cards.append((name, "INVALID_STATUS", "No valid status"))
            continue
        details = {
            "central_research": "Assets: " + str(report.get("asset_count", "unknown")) + "; as of: " + str(report.get("as_of_date", "unknown")),
            "small_budget": "Budget scenarios: " + ", ".join(sorted(report.get("budgets", {}))),
            "execution_costs": "Illustrative scenarios: " + str(len(report.get("scenarios", []))),
            "cost_adjusted": "Budgets compared: " + ", ".join(sorted(report.get("budgets", {}))),
            "decision_quality": "Forward validation: " + str(report.get("forward_validation", "NOT_ESTABLISHED")) + "; readiness: " + str(report.get("live_trading_readiness", "BLOCKED")),
            "forward_attribution": "Observed dates: " + str(report.get("observed_dates", 0)),
            "unified_evidence": "Blockers: " + ", ".join(report.get("blockers", [])),
        }
        cards.append((name, status, details[name]))
    body = "\n".join(
        "<section><h2>" + html.escape(name.replace("_", " ").title()) + "</h2><p><strong>" +
        html.escape(status) + "</strong></p><p>" + html.escape(details) + "</p></section>"
        for name, status, details in cards
    )
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Project E.T. Research Command Centre</title>'
            '<style>body{font-family:system-ui;background:#101827;color:#f1f5f9;max-width:960px;margin:auto;padding:24px}'
            'section{background:#1d2a3d;border:1px solid #41506a;border-radius:12px;margin:14px 0;padding:18px}'
            'h1{color:#8fd8ff}p{overflow-wrap:anywhere}.warning{background:#4a2b20;padding:14px;border-radius:8px}</style>'
            '</head><body><h1>Project E.T. — Research Command Centre</h1>'
            '<p class="warning">RESEARCH ONLY · ORDERS DISABLED · LIVE TRADING NOT APPROVED</p>' +
            body + '<p>Missing reports are not evidence of success. Historical simulation is not verified profitability.</p></body></html>')


def load_available_reports(folder="."):
    paths = {
        "central_research": "central_research_cycle.json",
        "small_budget": "small_budget_study.json",
        "execution_costs": "execution_cost_study.json",
        "cost_adjusted": "cost_adjusted_portfolio_study.json",
        "decision_quality": "decision_quality_audit.json",
        "forward_attribution": "forward_attribution_report.json",
        "unified_evidence": "portfolio_unified_evidence_review.json",
    }
    reports = {}
    for key, filename in paths.items():
        try:
            reports[key] = json.loads((Path(folder) / filename).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return reports


if __name__ == "__main__":
    Path("project_et_command_centre.html").write_text(build_command_centre(load_available_reports()), encoding="utf-8")
    print("Command centre created; missing evidence is labelled.")
