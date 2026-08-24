"""Basic 認証の HTTP ヘッダーを観察するためのローカル専用サーバー。"""

from __future__ import annotations

import argparse
import base64
import binascii
import hmac
import os
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Mapping, NoReturn


REALM = "Basic Auth Study"
CHALLENGE = f'Basic realm="{REALM}"'
DEFAULT_USERNAME = "study-user"
DEFAULT_PASSWORD = "study-password"
LOCAL_BIND_ADDRESS = "127.0.0.1"


@dataclass(frozen=True)
class AuthConfig:
    """起動時に一度だけ解決する、サーバーごとの資格情報。"""

    username: str
    password: str


def has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def validate_config_value(name: str, value: str, *, is_username: bool) -> str:
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(f"{name} は ASCII 文字だけを使用してください") from error
    if not value:
        raise ValueError(f"{name} は空にできません")
    if has_control_character(value):
        raise ValueError(f"{name} に制御文字は使用できません")
    if is_username and ":" in value:
        raise ValueError("BASIC_AUTH_USERNAME に ':' は使用できません")
    return value


def load_auth_config(environ: Mapping[str, str] | None = None) -> AuthConfig:
    """環境変数を一度だけ読み、サーバーに渡す不変設定を作る。"""

    source = os.environ if environ is None else environ
    username = validate_config_value(
        "BASIC_AUTH_USERNAME", source.get("BASIC_AUTH_USERNAME", DEFAULT_USERNAME), is_username=True
    )
    password = validate_config_value(
        "BASIC_AUTH_PASSWORD", source.get("BASIC_AUTH_PASSWORD", DEFAULT_PASSWORD), is_username=False
    )
    return AuthConfig(username=username, password=password)


def parse_basic_credentials(authorization: str | None) -> tuple[str, str] | None:
    """有効な Basic Authorization ヘッダーだけを (username, password) に変換する。"""

    if authorization is None:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "basic":
        return None
    try:
        decoded = base64.b64decode(parts[1], validate=True).decode("ascii")
    except (binascii.Error, UnicodeDecodeError):
        return None
    if ":" not in decoded:
        return None
    username, password = decoded.split(":", 1)
    if not username or has_control_character(username) or has_control_character(password) or ":" in username:
        return None
    return username, password


class BasicAuthHandler(BaseHTTPRequestHandler):
    server: "BasicAuthServer"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler の API 名に合わせる。
        if self.path == "/public":
            self.send_text(200, "public endpoint\n")
            return
        if self.path == "/protected":
            credentials = parse_basic_credentials(self.headers.get("Authorization"))
            if credentials is None or not self.credentials_match(credentials):
                self.request_authentication()
                return
            self.send_text(200, f"authenticated as {credentials[0]}\n")
            return
        self.send_text(404, "not found\n")

    def credentials_match(self, credentials: tuple[str, str]) -> bool:
        username, password = credentials
        config = self.server.auth_config
        username_matches = hmac.compare_digest(username, config.username)
        password_matches = hmac.compare_digest(password, config.password)
        return username_matches and password_matches

    def request_authentication(self) -> None:
        self.send_response(401)
        self.send_header("WWW-Authenticate", CHALLENGE)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_text(self, status: int, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        """学習用の出力を HTTP アクセスログで埋めない。"""


class BasicAuthServer(ThreadingHTTPServer):
    auth_config: AuthConfig


def create_server(config: AuthConfig, *, host: str = LOCAL_BIND_ADDRESS, port: int = 8000) -> BasicAuthServer:
    """ローカルループバック以外への bind を明示的に拒否する。"""

    if host != LOCAL_BIND_ADDRESS:
        raise ValueError(f"学習用サーバーは {LOCAL_BIND_ADDRESS} にのみ bind できます")
    server = BasicAuthServer((host, port), BasicAuthHandler)
    server.auth_config = config
    return server


def main() -> NoReturn:
    parser = argparse.ArgumentParser(description="ローカル専用 Basic 認証学習サーバー")
    parser.add_argument("--port", type=int, default=8000, help="待受ポート (既定: 8000)")
    args = parser.parse_args()
    config = load_auth_config()
    server = create_server(config, port=args.port)
    print(f"Listening on http://{LOCAL_BIND_ADDRESS}:{server.server_port}")
    print("Stop with Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()
    raise SystemExit(0)


if __name__ == "__main__":
    main()
