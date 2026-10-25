from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path


def main() -> None:
    # Export-only settings never connect to a database or become server defaults.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    os.environ.setdefault('MONGO_URI', 'mongodb://schema:export@localhost:27017/path')
    os.environ.setdefault('JWT_SECRET', secrets.token_hex(48))
    os.environ['ENVIRONMENT'] = 'test'
    from app.main import app

    destination = Path(__file__).resolve().parents[2] / 'docs' / 'openapi.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(app.openapi(), indent=2), encoding='utf-8', newline='\n')
    print(destination)


if __name__ == '__main__':
    main()
