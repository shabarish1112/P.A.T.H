"""Ensure default detectors find disposable fake secrets without printing values."""

from __future__ import annotations

import json
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / ".secrets.baseline").read_text(encoding="utf-8-sig"))
    assert len(baseline["plugins_used"]) > 0, "Secret detectors are disabled"
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="secret-probe-",
        dir=root,
        delete=False,
        encoding="utf-8",
    ) as output:
        path = Path(output.name)
        key = "AKIA" + "".join(
            secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(16)
        )
        output.write(
            f'aws_access_key_id = "{key}"\npassword = "{secrets.token_hex(32)}"\n'
        )
    try:
        result = subprocess.run(
            [sys.executable, "-m", "detect_secrets", "scan", "--all-files", path.name],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        count = sum(
            len(items) for items in json.loads(result.stdout)["results"].values()
        )
        assert count >= 2, "Default detectors failed to flag both planted fixtures"
        print(f"Planted-secret test passed: {count} findings; values suppressed.")
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
