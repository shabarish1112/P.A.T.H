from __future__ import annotations

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password
from app.repositories.users import UserRepository
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

    def update(self, user_id: str, body: UserUpdate) -> UserResponse:
        fields = body.model_dump(exclude_none=True)
        if 'role' in fields:
            fields['role'] = fields['role'].value
        user = self.repo.update(user_id, fields)
        if user is None:
            raise HTTPException(status_code=404, detail='User not found')
        return _serialize_user(user)
