from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password
from app.repositories.auth import AuthRepository
from app.repositories.leases import LeaseRepository
from app.repositories.users import UserRepository
from app.schemas.auth import AuthUser, PasswordReset
from app.schemas.users import UserCreate, UserResponse, UserUpdate


def _serialize_user(user: dict[str, object]) -> UserResponse:
    return UserResponse.model_validate({**user, 'id': str(user['_id'])})


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def create(self, body: UserCreate) -> UserResponse:
        try:
            doc = self.repo.create(body.email, hash_password(body.password), body.role.value)
        except DuplicateKeyError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='User already exists') from exc
        return _serialize_user(doc)

    def list(self) -> list[UserResponse]:
        return [_serialize_user(user) for user in self.repo.list()]

    def update(self, user_id: str, body: UserUpdate, actor: AuthUser) -> UserResponse:
        owner = uuid.uuid4().hex
        leases = LeaseRepository(self.repo.db)
        if not leases.acquire('admin_changes', owner, 30):
            raise HTTPException(status_code=409, detail='Another administrator update is in progress')
        try:
            current = self.repo.get_by_id(user_id)
            if current is None:
                raise HTTPException(status_code=404, detail='User not found')
            removing_admin = body.is_active is False or (body.role is not None and body.role.value != 'admin')
            if removing_admin and current['role'] == 'admin':
                if actor.id == user_id:
                    raise HTTPException(status_code=409, detail='You cannot deactivate or demote yourself')
                if (
                    current['is_active']
                    and self.repo.db.users.count_documents({'role': 'admin', 'is_active': True}) <= 1
                ):
                    raise HTTPException(
                        status_code=409, detail='The last active administrator must be retained'
                    )
            fields = body.model_dump(exclude_none=True, mode='json')
            user = self.repo.update(user_id, fields)
            AuthRepository(self.repo.db).revoke_all_for_user(user_id)
            if user is None:
                raise HTTPException(status_code=404, detail='User not found')
            return _serialize_user(user)
        finally:
            leases.release('admin_changes', owner)

    def reset_password(self, user_id: str, body: PasswordReset, actor: AuthUser) -> None:
        if actor.id == user_id:
            raise HTTPException(status_code=409, detail='Use change-password to change your own password')
        if self.repo.get_by_id(user_id) is None:
            raise HTTPException(status_code=404, detail='User not found')
        self.repo.update(
            user_id,
            {
                'password_hash': hash_password(body.new_password),
                'must_change_password': True,
            },
        )
        AuthRepository(self.repo.db).revoke_all_for_user(user_id)
