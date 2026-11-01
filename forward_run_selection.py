"""Select an archived snapshot old enough for the next market close.

The newest snapshot can still be waiting for a later close. Prefer the
previous completed snapshot when available, without assuming a second run
exists. The downstream evaluator independently checks newer close dates.
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
    eligible.sort(reverse=True)
    # With two or more snapshots, evaluate the previous completed run so
    # each daily cycle can observe a newer close. With only one, return it;
    # downstream evaluation reports PENDING until a later close exists.
    return eligible[1][1] if len(eligible) >= 2 else (eligible[0][1] if eligible else None)
