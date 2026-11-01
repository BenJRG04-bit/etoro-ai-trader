"""Validate full council report before publishing its dashboard."""
import json
from pathlib import Path
from council_report_integrity import validate_council_report
from council_accountability_dashboard import build_council_dashboard

def publish_validated_dashboard(directory="."):
    root = Path(directory)
    with (root / "council_accountability_report.json").open(encoding="utf-8") as handle:
        report = json.load(handle)
    integrity = validate_council_report(report)
    (root / "council_accountability_integrity.json").write_text(json.dumps(integrity, indent=2), encoding="utf-8")
    return build_council_dashboard(directory)

if __name__ == "__main__":
    print(publish_validated_dashboard())
