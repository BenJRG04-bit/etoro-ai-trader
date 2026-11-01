"""Read-only eToro Demo connectivity probe; never sends trading requests."""
import json
import os
import urllib.error
import urllib.request
import uuid

URL = "https://public-api.etoro.com/api/v1/trading/info/demo/pnl"

def check_demo_connection():
    public = os.environ.get("ETORO_PUBLIC_KEY", "")
    user = os.environ.get("ETORO_USER_KEY", "")
    if not public or not user:
        return {"connected": False, "reason": "Missing ETORO_PUBLIC_KEY or ETORO_USER_KEY"}
    request = urllib.request.Request(
        URL,
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
            # Do not print balances, credentials, or response bodies to CI logs.
            json.load(response)
            return {"connected": True, "environment": "demo", "read_only": True}
    except urllib.error.HTTPError as exc:
        return {"connected": False, "reason": "HTTP error", "status": exc.code}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"connected": False, "reason": type(exc).__name__}

if __name__ == "__main__":
    print(json.dumps(check_demo_connection()))
