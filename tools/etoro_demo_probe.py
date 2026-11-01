"""Read-only eToro DEMO connection probe. Never calls a real account or order endpoint."""
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

BASE = "https://public-api.etoro.com/api/v1"
PATHS = ("/watchlists/default-watchlists/items", "/trading/info/demo/portfolio", "/trading/info/demo/pnl")

def main():
    public = os.environ.get("ETORO_API_KEY", "").strip()
    user = os.environ.get("ETORO_USER_KEY", "").strip()
    if not public or not user:
        print("FAIL: missing ETORO_API_KEY or ETORO_USER_KEY GitHub secret")
        return 2
    for path in PATHS:
        req = urllib.request.Request(
            BASE + path,
            headers={"x-api-key": public, "x-user-key": user,
                     "x-request-id": str(uuid.uuid4()), "Accept": "application/json"},
            method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                # Never print response bodies: they may contain account details.
                response.read(1)
                print(f"{path}: HTTP {response.status} OK")
        except urllib.error.HTTPError as exc:
            print(f"{path}: HTTP {exc.code} (body withheld)")
            return 1
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"{path}: NETWORK ERROR ({type(exc).__name__})")
            return 1
    print("SUCCESS: read-only DEMO portfolio and PNL endpoints responded")
    return 0

if __name__ == "__main__":
    sys.exit(main())
