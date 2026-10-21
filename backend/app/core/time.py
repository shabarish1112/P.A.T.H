"""MongoDB stores UTC instants; legacy clients and mocks may decode them as naive."""

from datetime import UTC, datetime


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
