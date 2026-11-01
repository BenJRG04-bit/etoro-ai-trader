import unittest
from unittest.mock import patch
import urllib.error
from tools.check_etoro_account_read_access import check_read_access, diagnose


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False


class DiagnosticsTests(unittest.TestCase):
    def test_all_403(self):
        def denied(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)
        result = check_read_access("public", "user", opener=denied)
        self.assertEqual(result, {"watchlist": 403, "market_data": 403, "identity": 403, "demo": 403})
        self.assertEqual(diagnose(result), "ALL_403_CHECK_API_ENTITLEMENT_SCOPES_IP_OR_SUPPORT")

    def test_demo_success(self):
        result = check_read_access("public", "user", opener=lambda req, timeout: Response())
        self.assertEqual(diagnose(result), "DEMO_READ_OK")

    def test_missing_keys(self):
        self.assertEqual(check_read_access("", "user"), {"error": "MISSING_KEY_SECRETS"})

    def test_headers_and_read_only(self):
        seen = []
        def opener(req, timeout):
            seen.append(req)
            return Response()
        check_read_access("public", "user", opener=opener)
        self.assertEqual(len(seen), 4)
        self.assertTrue(all(req.get_method() == "GET" for req in seen))
        self.assertTrue(all(req.get_header("X-api-key") == "public" for req in seen))
        self.assertTrue(all(req.get_header("X-user-key") == "user" for req in seen))
        self.assertEqual(len({req.get_header("X-request-id") for req in seen}), 4)


if __name__ == "__main__":
    unittest.main()
