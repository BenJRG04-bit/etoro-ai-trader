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


# The snapshot schema was introduced on 1 November 2026.
# Earlier successful pattern-research artifacts do not contain a frozen snapshot.
FIRST_SUPPORTED_ARCHIVE_UTC = "2026-11-01T18:34:00Z"


def select_mature_pattern_runs(runs, *, evaluated_at, minimum_age_hours=48,
                               max_runs=30,
                               first_supported_at=FIRST_SUPPORTED_ARCHIVE_UTC):
    """Select a BATCH of eligible archives so weekends never skip predictions.

    Returning only the most recent aged run can permanently omit Thursday
    predictions when Friday's run becomes age-eligible over the weekend.
    A bounded rolling set scores each archived observation repeatedly until
    it is observed, and the cumulative scorecard deduplicates dates.
    """
    if (not isinstance(runs, list) or type(max_runs) is not int
        or not 1 <= max_runs <= 60 or type(minimum_age_hours) is not int
        or minimum_age_hours < 24):
        raise ValueError("Invalid archive selection request")
    if not isinstance(evaluated_at, str):
        raise ValueError("Missing evaluation timestamp")
    try:
        now = datetime.fromisoformat(evaluated_at.replace("Z", "+00:00"))
        introduced = datetime.fromisoformat(first_supported_at.replace("Z", "+00:00"))
        if now.tzinfo is None or introduced.tzinfo is None:
            raise ValueError("Missing timezone")
        now = now.astimezone(timezone.utc)
        introduced = introduced.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Invalid archive selection timestamp") from exc
    cutoff = now - timedelta(hours=minimum_age_hours)
    eligible = []
    ids = set()
    for row in runs:
        if (not isinstance(row, dict) or row.get("status") != "completed"
            or row.get("conclusion") != "success"
            or row.get("head_branch") != "main"):
            continue
        try:
            rid = row["id"]
            created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            completed = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
            if (type(rid) is not int or rid <= 0 or rid in ids
                or created.tzinfo is None or completed.tzinfo is None):
                continue
            created = created.astimezone(timezone.utc)
            completed = completed.astimezone(timezone.utc)
            if created < introduced or not created <= completed <= cutoff:
                continue
        except (TypeError, KeyError, ValueError, AttributeError):
            continue
        ids.add(rid)
        eligible.append((completed, rid))
    eligible.sort(reverse=True)
    return [rid for _, rid in eligible[:max_runs]]
