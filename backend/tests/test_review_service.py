from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.schemas.auth import AuthUser
from app.schemas.enums import ReviewStatus, Role
from app.schemas.reviews import ReviewBody
from app.services.review_service import ReviewService


class FakeSettingsRepo:
    def get(self, key: str):
        return 'run-1' if key == 'active_run_id' else None


class FakeCache:
    def invalidate(self, prefix: str) -> None:
        self.prefix = prefix


class FakeReviews:
    def __init__(self) -> None:
        self.events = []

    def latest(self, run_id: str, transaction_id: str):
        return self.events[-1] if self.events else None

    def create(self, doc: dict):
        out = {**doc, '_id': str(len(self.events) + 1), 'created_at': datetime.now(UTC)}
        self.events.append(out)
        return out


def actor(user_id: str, role: Role) -> AuthUser:
    return AuthUser(id=user_id, email=f'{user_id}@example.com', role=role, is_active=True)


def test_reviewer_separation_of_duties_requires_second_actor() -> None:
    repo = FakeReviews()
    service = ReviewService(repo, FakeSettingsRepo(), FakeCache())
    reviewer = actor('r1', Role.reviewer)
    other = actor('r2', Role.reviewer)

    service.create(
        'TX-1',
        ReviewBody(status=ReviewStatus.escalated, note='Escalate'),
        reviewer,
    )
    with pytest.raises(HTTPException) as exc:
        service.create(
            'TX-1',
            ReviewBody(status=ReviewStatus.false_alert, note='Reverse my own decision'),
            reviewer,
        )
    assert exc.value.status_code == 409

    service.create(
        'TX-1',
        ReviewBody(status=ReviewStatus.pending_review, note='Second-person review'),
        other,
    )
    result = service.create(
        'TX-1',
        ReviewBody(status=ReviewStatus.false_alert, note='Now permitted'),
        reviewer,
    )
    assert result.status == ReviewStatus.false_alert
