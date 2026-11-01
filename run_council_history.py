"""Summarize archived daily council accountability JSON files offline."""
import json
import sys
from pathlib import Path
from council_history_trends import summarize_council_history

def run_history(paths):
    reports = []
    for path in paths:
        source = Path(path)
        if source.is_dir():
            for candidate in sorted(source.rglob("council_accountability_report.json")):
                with candidate.open(encoding="utf-8") as f:
                    reports.append(json.load(f))
        else:
            with source.open(encoding="utf-8") as f:
                reports.append(json.load(f))
    return summarize_council_history(reports)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python run_council_history.py <archive-dir-or-report.json> [...]")
    print(json.dumps(run_history(sys.argv[1:]), indent=2))
