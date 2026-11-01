"""Safely diagnose eToro Demo API read permissions; GET requests only.

No response bodies, account data, or credentials are printed.
"""
import os
import sys
import urllib.error
import urllib.request
import uuid

BASE = "https://public-api.etoro.com/api/v1"
PATHS = (
    "/trading/info/demo/portfolio",
    "/trading/info/demo/pnl",
)

def main():
    public = os.environ.get("ETORO_API_KEY", "").strip()
    user = os.environ.get("ETORO_USER_KEY", "").strip()
    if not public or not user:
        print("FAIL: missing GitHub API key secret(s)")
        return 2
    successes = 0
    for path in PATHS:
        request = urllib.request.Request(
            BASE + path,
            headers={
                "x-api-key": public,
                "x-user-key": user,
                "x-request-id": str(uuid.uuid4()),
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response.read(1)
                print(f"{path}: HTTP {response.status} OK")
                successes += 1
        except urllib.error.HTTPError as exc:
            print(f"{path}: HTTP {exc.code} (body withheld)")
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"{path}: NETWORK ERROR ({type(exc).__name__})")
    if successes == len(PATHS):
        print("SUCCESS: Both read-only Demo endpoints responded.")
        return 0
    print("FAIL: Demo read access is not fully verified. No orders attempted.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
