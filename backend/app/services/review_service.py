from __future__ import annotations

from fastapi import HTTPException, status

from app.core.cache import CacheBackend
from app.repositories.reviews import ReviewRepository
from app.repositories.settings import SettingsRepository
from app.schemas.auth import AuthUser
from app.schemas.enums import ReviewStatus, Role
from app.schemas.reviews import ReviewBody, ReviewResponse


class ReviewService:
    def __init__(self, repo: ReviewRepository, settings_repo: SettingsRepository, cache: CacheBackend) -> None:
        self.repo = repo
        self.settings_repo = settings_repo
        self.cache = cache

    def create(self, transaction_id: str, body: ReviewBody, actor: AuthUser) -> ReviewResponse:
        run_id = self.settings_repo.get('active_run_id')
        if not run_id:
            raise HTTPException(status_code=409, detail='No active model run')
        latest = self.repo.latest(run_id, transaction_id)
        protected = {ReviewStatus.confirmed_finding.value, ReviewStatus.escalated.value}
        if (
            actor.role == Role.reviewer
            and latest
            and latest.get('actor_id') == actor.id
            and latest.get('status') in protected
            and body.status.value != latest.get('status')
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Separation of duties: another reviewer or admin must record the next action after your confirmed/escalated decision',
            )
        doc = self.repo.create(
            {
                'transaction_id': transaction_id,
                'run_id': run_id,
                'status': body.status.value,
                'note': body.note.strip(),
                'actor_id': actor.id,
                'actor_email': actor.email,
            }
        )
        self.cache.invalidate('analytics:')
        return ReviewResponse(
            id=str(doc['_id']),
            transaction_id=transaction_id,
            run_id=run_id,
            status=doc['status'],
            note=doc['note'],
            actor_id=doc['actor_id'],
            actor_email=doc['actor_email'],
            created_at=doc['created_at'],
        )

    def list(self, limit: int) -> list[ReviewResponse]:
        run_id = self.settings_repo.get('active_run_id')
        if not run_id:
            return []
        return [
            ReviewResponse(
                id=str(doc['_id']),
                transaction_id=str(doc['transaction_id']),
                run_id=str(doc['run_id']),
                status=str(doc['status']),
                note=str(doc.get('note', '')),
                actor_id=str(doc['actor_id']),
                actor_email=str(doc['actor_email']),
                created_at=doc['created_at'],
            )
            for doc in self.repo.list(run_id, limit)
        ]
