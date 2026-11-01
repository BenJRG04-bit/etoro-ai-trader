"""Select the newest completed prior snapshot run, not blindly the second run.

The evaluator's run is not a snapshot run. Selecting index 1 incorrectly
skips the newest available archived snapshot and can delay forward evidence.
"""
from datetime import datetime, timezone

def select_prior_snapshot_run(runs, *, evaluation_started_at):
    if not isinstance(runs, list):
        raise ValueError("Invalid runs")
    try:
        cutoff = datetime.fromisoformat(evaluation_started_at.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("Invalid evaluation start") from exc
    if cutoff.tzinfo is None:
        raise ValueError("Evaluation start must have timezone")
    eligible = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        if run.get("head_branch") != "main":
            continue
        try:
            completed = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            run_id = run["id"]
            if type(run_id) is not int or run_id <= 0 or completed.tzinfo is None:
                continue
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if completed < cutoff:
            eligible.append((completed, run_id))
    return max(eligible)[1] if eligible else None
