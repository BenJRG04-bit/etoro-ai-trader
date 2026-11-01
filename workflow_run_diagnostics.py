"""Audit actual GitHub Actions workflow run metadata without claiming market success."""
from datetime import datetime, timezone

WORKFLOWS = {
    "council-accountability.yml": "daily_six_brain_research",
    "council-history.yml": "archived_council_history",
    "forward-signals.yml": "daily_forward_snapshots",
    "forward-batch-audit.yml": "forward_archive_audit",
    "research-readiness.yml": "combined_readiness",
}

def summarize_workflow_runs(runs, *, now=None, max_age_hours=96):
    if not isinstance(runs, list):
        raise ValueError("Invalid workflow run list")
    if type(max_age_hours) is not int or not 1 <= max_age_hours <= 24 * 30:
        raise ValueError("Invalid maximum age")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Time must be timezone-aware")
    output = {}
    for filename, label in WORKFLOWS.items():
        matches = [row for row in runs if isinstance(row, dict)
                   and row.get("path", "").split("/")[-1] == filename
                   and row.get("head_branch") == "main"]
        matches.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        if not matches:
            output[label] = {"status": "NO_RUN_FOUND", "workflow": filename}
            continue
        row = matches[0]
        created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        if created.tzinfo is None or created > current:
            raise ValueError("Invalid workflow timestamp")
        age_hours = round((current - created).total_seconds() / 3600, 2)
        status = "SUCCESS" if row.get("status") == "completed" and row.get("conclusion") == "success" else "INCOMPLETE_OR_FAILED"
        if age_hours > max_age_hours:
            status = "STALE_RUN"
        output[label] = {"status": status, "workflow": filename, "run_id": row.get("id"),
                         "age_hours": age_hours, "event": row.get("event"),
                         "conclusion": row.get("conclusion")}
    blockers = [label for label, row in output.items() if row["status"] != "SUCCESS"]
    return {"status": "WORKFLOW_RUNS_PRESENT" if not blockers else "WORKFLOW_VERIFICATION_INCOMPLETE",
            "workflows": output, "blockers": blockers, "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "limitations": "GitHub run metadata only. A successful job does not prove data quality, profitability, or readiness to trade."}
