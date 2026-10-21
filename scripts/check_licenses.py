"""Reject unapproved reciprocal licenses in generated transitive inventories."""

from __future__ import annotations

import json
import re
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    inventory = root / "docs" / "licenses"
    python = json.loads((inventory / "python.json").read_text())
    npm = json.loads((inventory / "npm.json").read_text())
    entries = [(f"{p['Name']}@{p['Version']}", p["License"]) for p in python]
    entries.extend(
        (name, str(value.get("licenses", "UNKNOWN"))) for name, value in npm.items()
    )
    allowed = json.loads((inventory / "allowlist.json").read_text())
    failures = [
        name
        for name, license_name in entries
        if re.search(r"\b(?:GPL|AGPL)(?:-|\s|$)", license_name, re.IGNORECASE)
        and name not in allowed
    ]
    if failures:
        raise SystemExit("Unapproved GPL/AGPL dependencies: " + ", ".join(failures))
    print(f"License policy passed for {len(entries)} dependency records.")


if __name__ == "__main__":
    main()
