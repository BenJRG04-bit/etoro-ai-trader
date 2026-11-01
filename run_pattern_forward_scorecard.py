"""Build a conservative summary from archived GitHub Actions evaluation JSON files.

The input directory must contain files named pattern_forward_evaluation.json,
each downloaded from a completed GitHub Actions run. Never use broker data.
"""
from pathlib import Path
import json
import sys

from pattern_forward_scorecard import SAFE, summarize_pattern_forward_outcomes


def run_scorecard(directory):
    directory = Path(directory)
    try:
        if not directory.is_dir():
            raise ValueError("Missing archive directory")
        paths = sorted(directory.rglob("pattern_forward_evaluation.json"))
        documents = []
        for path in paths:
            with path.open(encoding="utf-8") as handle:
                documents.append(json.load(handle))
        summary = summarize_pattern_forward_outcomes(documents)
        manifest_path = directory / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("Invalid archive manifest")
            downloaded = manifest.get("downloaded")
            unavailable = manifest.get("unavailable", [])
            if (type(downloaded) is not int or downloaded != len(paths)
                or not isinstance(unavailable, list)
                or any(type(id) is not int or id <= 0 for id in unavailable)):
                raise ValueError("Inconsistent archive manifest")
            summary["archived_runs_loaded"] = downloaded
            summary["unavailable_archived_runs"] = len(unavailable)
            if unavailable:
                summary["status"] = "INCOMPLETE_ARCHIVE_SET"
                summary["blockers"] = sorted(set(summary["blockers"] + ["MISSING_ARCHIVED_RUNS"]))
        else:
            summary["archived_runs_loaded"] = len(paths)
            summary["unavailable_archived_runs"] = 0
        return summary
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        return {**SAFE, "status": "INVALID_INPUTS",
                "error_type": type(exc).__name__,
                "blockers": ["CANNOT_VERIFY_ALL_ARCHIVED_OUTCOMES"]}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python run_pattern_forward_scorecard.py <archive_directory>")
    print(json.dumps(run_scorecard(sys.argv[1]), indent=2))
