"""Tests that account connectivity checks are strictly read-only."""
import io
import unittest
import urllib.error
from tools.check_etoro_account_read_access import check_read_access


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False


class ReadOnlyProbeTests(unittest.TestCase):
    def test_checks_watchlist_identity_and_demo_with_get_only(self):
        requested = []

        def opener(request, timeout):
            self.assertEqual(timeout, 15)
            self.assertEqual(request.get_method(), "GET")
            self.assertTrue(request.full_url.startswith("https://public-api.etoro.com/api/v1/"))
            self.assertEqual(request.get_header("X-api-key"), "public")
            self.assertEqual(request.get_header("X-user-key"), "user")
            requested.append(request.full_url)
            return Response()

        result = check_read_access("public", "user", opener)
        self.assertEqual(result, {"watchlist": 200, "market_data": 200, "identity": 200, "demo": 200})
        self.assertEqual(len(requested), 4)

    def test_http_403_reports_only_code(self):
        def opener(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO(b"private"))
        result = check_read_access("public", "user", opener)
        self.assertEqual(result, {"watchlist": 403, "market_data": 403, "identity": 403, "demo": 403})
        self.assertNotIn("private", repr(result))

    def test_missing_keys_never_send_request(self):
        def opener(*args, **kwargs):
            self.fail("network request should never happen")
        self.assertEqual(check_read_access("", "user", opener), {"error": "MISSING_KEY_SECRETS"})


if __name__ == "__main__":
    unittest.main()
