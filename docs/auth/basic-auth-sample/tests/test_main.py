from __future__ import annotations

import base64
import hmac
import http.client
import pathlib
import sys
import threading
import unittest
from unittest.mock import patch

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from main import CHALLENGE, AuthConfig, create_server  # noqa: E402


def basic_header(username: str, password: str, *, scheme: str = "Basic") -> str:
    token = base64.b64encode(f"{username}:{password}".encode("ascii")).decode("ascii")
    return f"{scheme} {token}"


class BasicAuthServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AuthConfig(username="learner", password="secret:with-colon")
        self.server = create_server(self.config, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def request(self, path: str, authorization: str | None = None) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        headers = {} if authorization is None else {"Authorization": authorization}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def assert_unauthorized(self, authorization: str | None) -> None:
        status, headers, body = self.request("/protected", authorization)
        self.assertEqual(status, 401)
        self.assertEqual(headers.get("WWW-Authenticate"), CHALLENGE)
        self.assertEqual(body, b"")

    def test_public_does_not_require_authentication(self) -> None:
        status, headers, body = self.request("/public")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)
        self.assertEqual(body, b"public endpoint\n")

    def test_missing_credentials_returns_challenge(self) -> None:
        self.assert_unauthorized(None)

    def test_correct_credentials_are_accepted(self) -> None:
        status, _, body = self.request("/protected", basic_header("learner", "secret:with-colon"))
        self.assertEqual(status, 200)
        self.assertEqual(body, b"authenticated as learner\n")

    def test_wrong_credentials_return_the_same_challenge(self) -> None:
        self.assert_unauthorized(basic_header("learner", "wrong"))

    def test_both_credentials_are_compared_when_username_is_wrong(self) -> None:
        with patch("main.hmac.compare_digest", wraps=hmac.compare_digest) as compare_digest:
            self.assert_unauthorized(basic_header("wrong-user", "wrong-password"))
        self.assertEqual(compare_digest.call_count, 2)

    def test_invalid_base64_returns_the_same_challenge(self) -> None:
        self.assert_unauthorized("Basic not-valid-base64!")

    def test_non_basic_scheme_returns_the_same_challenge(self) -> None:
        self.assert_unauthorized("Bearer token")

    def test_scheme_is_case_insensitive(self) -> None:
        status, _, _ = self.request("/protected", basic_header("learner", "secret:with-colon", scheme="basic"))
        self.assertEqual(status, 200)

    def test_password_can_contain_colon(self) -> None:
        status, _, _ = self.request("/protected", basic_header("learner", "secret:with-colon"))
        self.assertEqual(status, 200)

    def test_missing_colon_returns_the_same_challenge(self) -> None:
        token = base64.b64encode(b"learner").decode("ascii")
        self.assert_unauthorized(f"Basic {token}")

    def test_control_characters_return_the_same_challenge(self) -> None:
        self.assert_unauthorized(basic_header("learner\nadmin", "secret"))
        self.assert_unauthorized(basic_header("learner", "secret\nvalue"))

    def test_server_only_allows_loopback_bind(self) -> None:
        with self.assertRaises(ValueError):
            create_server(self.config, host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
