"""Fetch each research workflow separately to avoid losing runs in busy repositories."""
import json
import os
import urllib.request
from workflow_run_diagnostics import WORKFLOWS, summarize_workflow_runs

def run_diagnostics(repo, token, fetch=None):
    if not isinstance(repo, str) or len(repo.split("/")) != 2 or not all(repo.split("/")) or not token:
        raise ValueError("Repository and read-only Actions token required")
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "User-Agent": "project-et-research-diagnostics"}
    if fetch is None:
        def fetch(target, headers):
            with urllib.request.urlopen(urllib.request.Request(target, headers=headers), timeout=25) as response:
                return json.load(response)
    runs = []
    errors = {}
    for filename in WORKFLOWS:
        url = "https://api.github.com/repos/" + repo + "/actions/workflows/" + filename + "/runs?branch=main&per_page=5"
        try:
            payload = fetch(url, headers)
            if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
                raise ValueError("Malformed GitHub Actions response")
            for row in payload["workflow_runs"]:
                if not isinstance(row, dict):
                    raise ValueError("Malformed workflow run")
                item = dict(row)
                item["path"] = ".github/workflows/" + filename
                runs.append(item)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors[WORKFLOWS[filename]] = type(exc).__name__
    report = summarize_workflow_runs(runs)
    for label, error in errors.items():
        report["workflows"][label] = {"status": "FETCH_ERROR", "workflow": next(k for k, v in WORKFLOWS.items() if v == label), "error_type": error}
    report["blockers"] = [label for label, item in report["workflows"].items() if item["status"] != "SUCCESS"]
    report["status"] = "WORKFLOW_VERIFICATION_INCOMPLETE" if report["blockers"] else "WORKFLOW_RUNS_PRESENT"
    return report

if __name__ == "__main__":
    print(json.dumps(run_diagnostics(os.environ["GH_REPO"], os.environ["GH_TOKEN"]), indent=2))
