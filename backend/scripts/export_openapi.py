from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> None:
    destination = Path(__file__).resolve().parents[2] / 'docs' / 'openapi.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(app.openapi(), indent=2), encoding='utf-8')
    print(destination)


if __name__ == '__main__':
    main()
