"""Produce read-only council history quality JSON and HTML dashboard."""
import json
from pathlib import Path
from council_history_quality import assess_history_quality
from council_history_dashboard import build_council_history_dashboard

def publish_history(directory="."):
    root = Path(directory)
    with (root / "council_history_report.json").open(encoding="utf-8") as handle:
        report = json.load(handle)
    quality = assess_history_quality(report)
    (root / "council_history_quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    return build_council_history_dashboard(directory)

if __name__ == "__main__":
    print(publish_history())
