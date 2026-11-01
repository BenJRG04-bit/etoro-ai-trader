"""Validate expected GitHub Actions research artifacts from run metadata.

Artifact presence is not proof of correctness, observed evidence or profitability.
"""
EXPECTED_ARTIFACTS = {
    "daily_six_brain_research": "project-et-council-accountability",
    "archived_council_history": "project-et-council-history",
    "daily_forward_snapshots": "project-et-forward-signals",
    "forward_archive_audit": "project-et-forward-batch-audit",
    "combined_readiness": "project-et-research-readiness",
}

def verify_pipeline_artifacts(report, fetch, repo, headers):
    if not isinstance(report, dict) or report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe pipeline report")
    if not isinstance(report.get("workflows"), dict) or set(report["workflows"]) != set(EXPECTED_ARTIFACTS):
        raise ValueError("Invalid workflow set")
    for label, expected in EXPECTED_ARTIFACTS.items():
        item = report["workflows"][label]
        if item.get("status") != "SUCCESS":
            item["artifact_status"] = "NOT_CHECKED"
            continue
        run_id = item.get("run_id")
        if type(run_id) is not int or run_id < 1:
            item["artifact_status"] = "INVALID_RUN_ID"
            continue
        url = "https://api.github.com/repos/" + repo + "/actions/runs/" + str(run_id) + "/artifacts?per_page=100"
        try:
            payload = fetch(url, headers)
            if not isinstance(payload, dict) or not isinstance(payload.get("artifacts"), list):
                raise ValueError("Invalid artifact response")
            matches = [a for a in payload["artifacts"] if isinstance(a, dict) and a.get("name") == expected
                       and a.get("expired") is False and type(a.get("size_in_bytes")) is int
                       and a["size_in_bytes"] > 0]
            item["artifact_status"] = "PRESENT" if matches else "MISSING_OR_EXPIRED"
        except (OSError, ValueError, TypeError, KeyError):
            item["artifact_status"] = "FETCH_ERROR"
    report["blockers"] = [label for label, item in report["workflows"].items()
                          if item["status"] != "SUCCESS" or item.get("artifact_status") != "PRESENT"]
    report["status"] = "WORKFLOW_RUNS_PRESENT" if not report["blockers"] else "WORKFLOW_VERIFICATION_INCOMPLETE"
    report["limitations"] = "Checks recent GitHub workflow runs and named nonempty artifacts only; not the artifact content, market accuracy, profit or live trading readiness."
    return report
