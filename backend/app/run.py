"""Explicit trusted-proxy and worker configuration for every deployment."""

import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        'app.main:app',
        host=settings.host,
        port=8000,
        workers=settings.workers,
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
    )


if __name__ == '__main__':
    main()
