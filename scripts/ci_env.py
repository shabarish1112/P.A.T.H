"""Create disposable CI credentials without emitting their values."""

from __future__ import annotations

import os
import secrets
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    app_password = secrets.token_hex(32)
    admin_password = secrets.token_urlsafe(32)
    values = {
        "infra/mongo.env": (
            f"MONGO_ROOT_USER=ci_root\nMONGO_ROOT_PASSWORD={secrets.token_hex(32)}\n"
            f"PATH_APP_USER=path_app\nPATH_APP_PASSWORD={app_password}\n"
        ),
        "backend/.env": (
            f"MONGO_URI=mongodb://path_app:{app_password}@mongo:27017/path?authSource=path\n"
            f"JWT_SECRET={secrets.token_hex(48)}\nENVIRONMENT=test\nHOST=0.0.0.0\n"
            "MONGO_DB=path\nCORS_ORIGINS=http://localhost:5173\n"
        ),
    }
    for name, content in values.items():
        with (root / name).open("x", encoding="utf-8") as output:
            output.write(content)
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with Path(github_env).open("a", encoding="utf-8") as output:
            output.write(
                f"E2E_EMAIL=e2e-admin@example.com\nE2E_PASSWORD={admin_password}\n"
            )
    print("Ephemeral service credentials generated; values are not logged.")


if __name__ == "__main__":
    main()
