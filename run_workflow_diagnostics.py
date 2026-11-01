"""Fetch read-only GitHub Actions metadata for Project E.T. pipeline diagnostics."""
import json
import os
import urllib.request
from workflow_run_diagnostics import summarize_workflow_runs

def run_diagnostics(repo, token, fetch=None):
    if not repo or "/" not in repo or not token:
        raise ValueError("Repository and read-only Actions token required")
    url = "https://api.github.com/repos/" + repo + "/actions/runs?branch=main&per_page=100"
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "User-Agent": "project-et-research-diagnostics"}
    if fetch is None:
        def fetch(target, headers):
            with urllib.request.urlopen(urllib.request.Request(target, headers=headers), timeout=25) as response:
                return json.load(response)
    payload = fetch(url, headers)
    if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
        raise ValueError("Malformed GitHub Actions response")
    return summarize_workflow_runs(payload["workflow_runs"])

if __name__ == "__main__":
    print(json.dumps(run_diagnostics(os.environ["GH_REPO"], os.environ["GH_TOKEN"]), indent=2))
