"""Select only older, successful MAIN-branch pattern artifact runs.

This is an archive discovery helper, not a proof of strategy quality.
The downstream evaluator verifies the snapshot timestamp, signal date, first
possible entry date, subsequent closes and all research-only safety flags.
"""
from datetime import datetime, timedelta, timezone


def select_prior_pattern_run(runs, *, evaluated_at, minimum_age_hours=48):
    if not isinstance(runs, list) or (type(minimum_age_hours) is not int or
                                      minimum_age_hours < 24):
        raise ValueError("Invalid archive query")
    if not isinstance(evaluated_at, str):
        raise ValueError("Timezone-aware evaluation time required")
    try:
        now = datetime.fromisoformat(evaluated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid evaluation time") from exc
    if now.tzinfo is None:
        raise ValueError("Evaluation time must be timezone-aware")
    cutoff = now.astimezone(timezone.utc) - timedelta(hours=minimum_age_hours)
    eligible = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        if run.get("head_branch") != "main":
            continue
        try:
            run_id = run["id"]
            stamp = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            if (type(run_id) is not int or run_id <= 0 or
                stamp.tzinfo is None or stamp.astimezone(timezone.utc) > cutoff):
                continue
        except (TypeError, KeyError, ValueError, AttributeError):
            continue
        eligible.append((stamp.astimezone(timezone.utc), run_id))
    if not eligible:
        return None
    return max(eligible)[1]
