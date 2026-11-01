"""Safe, read-only eToro API key diagnostics.

Tests the documented first-call watchlist, identity and demo portfolio routes.
Never sends trading orders, reads response bodies, or logs credentials.
"""
import os
import sys
import urllib.error
import urllib.request
import uuid

BASE = "https://public-api.etoro.com/api/v1"
ENDPOINTS = (
    ("watchlist", "/watchlists/default-watchlists/items"),
    ("identity", "/me"),
    ("demo", "/trading/info/demo/portfolio"),
)


def check_read_access(public_key, user_key, opener=urllib.request.urlopen):
    if not public_key or not user_key:
        return {"error": "MISSING_KEY_SECRETS"}
    results = {}
    for label, path in ENDPOINTS:
        request = urllib.request.Request(
            BASE + path,
            headers={
                "x-api-key": public_key,
                "x-user-key": user_key,
                "x-request-id": str(uuid.uuid4()),
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=15) as response:
                results[label] = int(response.status)
        except urllib.error.HTTPError as exc:
            results[label] = int(exc.code)
            exc.close()
        except (urllib.error.URLError, TimeoutError, OSError):
            results[label] = "NETWORK_ERROR"
    return results


def diagnose(result):
    if result.get("demo") == 200:
        return "DEMO_READ_OK"
    if result.get("watchlist") == 200:
        return "WATCHLIST_OK_DEMO_DENIED_CHECK_DEMO_SCOPES"
    if result.get("identity") == 200:
        return "IDENTITY_OK_OTHER_READS_DENIED_CHECK_SCOPES"
    if all(result.get(k) == 403 for k in ("watchlist", "identity", "demo")):
        return "ALL_403_CHECK_KEY_PAIR_ENTITLEMENTS_OR_SOURCE_IP"
    if any(result.get(k) == "NETWORK_ERROR" for k in ENDPOINT_LABELS):
        return "NETWORK_ERROR_CHECK_GITHUB_CONNECTIVITY"
    return "AUTH_UNCONFIRMED_CHECK_PUBLIC_KEY_USER_KEY_PAIR"


ENDPOINT_LABELS = tuple(label for label, _ in ENDPOINTS)


def main():
    public_key = os.getenv("ETORO_API_KEY", "").strip()
    user_key = os.getenv("ETORO_USER_KEY", "").strip()
    result = check_read_access(public_key, user_key)
    if "error" in result:
        print("FAIL: Required GitHub secrets are missing or blank.")
        return 2
    for label in ENDPOINT_LABELS:
        print(f"{label.upper()}_READ: {result[label]}")
    print("DIAGNOSIS:", diagnose(result))
    print("NO_ORDERS_ATTEMPTED: true")
    return 0 if result.get("demo") == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
