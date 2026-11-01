"""Read-only authentication diagnosis for the eToro Public API.

Checks REAL and DEMO portfolio read endpoints with the GitHub Actions key pair.
No order endpoints, POST requests, account values, tokens or response bodies.
This diagnostic must NEVER be reused as a trading execution module.
"""
import os
import sys
import urllib.error
import urllib.request
import uuid

BASE = "https://public-api.etoro.com/api/v1"
ENDPOINTS = (
    ("real", "/trading/info/portfolio"),
    ("demo", "/trading/info/demo/portfolio"),
)


def check_read_access(public_key, user_key, opener=urllib.request.urlopen):
    if not public_key or not user_key:
        return {"error": "MISSING_KEY_SECRETS"}
    results = {}
    for account_type, path in ENDPOINTS:
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
                # Read nothing from the response to avoid processing private account data.
                results[account_type] = int(response.status)
        except urllib.error.HTTPError as exc:
            results[account_type] = int(exc.code)
            exc.close()
        except (urllib.error.URLError, TimeoutError, OSError):
            results[account_type] = "NETWORK_ERROR"
    return results


def main():
    public_key = os.getenv("ETORO_API_KEY", "").strip()
    user_key = os.getenv("ETORO_USER_KEY", "").strip()
    result = check_read_access(public_key, user_key)
    if "error" in result:
        print("FAIL: Required GitHub secrets are missing or blank.")
        return 2
    for account, code in result.items():
        print(f"{account.upper()}_READ: {code}")
    if result.get("real") == 200 and result.get("demo") != 200:
        print("DIAGNOSIS: Real reading works through GitHub; demo reading is denied.")
    elif result.get("demo") == 200 and result.get("real") != 200:
        print("DIAGNOSIS: Demo reading works through GitHub; real reading is denied.")
    elif result.get("real") == 200 and result.get("demo") == 200:
        print("DIAGNOSIS: Both account read endpoints respond successfully.")
    else:
        print("DIAGNOSIS: Neither account read endpoint is available with these GitHub secrets.")
    print("NO_ORDERS_ATTEMPTED: true")
    return 0 if 200 in result.values() else 1


if __name__ == "__main__":
    sys.exit(main())
