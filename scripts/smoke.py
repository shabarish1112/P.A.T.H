"""Check readiness, anonymous denial and role boundaries against a running stack."""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request


def request(
    path: str,
    data: bytes | None = None,
    token: str | None = None,
    content_type: str = "application/json",
) -> tuple[int, dict[str, object]]:
    headers = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    message = urllib.request.Request(
        "http://127.0.0.1:5173" + path, data=data, headers=headers
    )
    try:
        with urllib.request.urlopen(message, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def login(email: str, password: str) -> str:
    code, response = request(
        "/api/auth/login",
        urllib.parse.urlencode(
            {
                "username": email,
                "password": password,
            }
        ).encode(),
        content_type="application/x-www-form-urlencoded",
    )
    assert code == 200, f"Login failed: {code}"
    return str(response["access_token"])


def main() -> None:
    assert request("/health/ready")[0] == 200
    assert request("/api/audit")[0] == 401
    token = login(os.environ["E2E_EMAIL"], os.environ["E2E_PASSWORD"])
    assert request("/api/audit", token=token)[0] == 200
    password = secrets.token_urlsafe(32)
    email = f"smoke-{secrets.token_hex(4)}@example.com"
    assert (
        request(
            "/api/users",
            json.dumps(
                {
                    "email": email,
                    "password": password,
                    "role": "analyst",
                }
            ).encode(),
            token,
        )[0]
        == 201
    )
    analyst = login(email, password)
    assert request("/api/audit", token=analyst)[0] == 403
    print("Readiness and authentication smoke: 200 / 401 / 403 boundaries passed.")


if __name__ == "__main__":
    main()
