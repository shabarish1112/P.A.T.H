from __future__ import annotations

from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class Pagination(BaseModel):
    limit: int = 50
    cursor: str | None = None


def pagination_params(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=64)] = None,
) -> Pagination:
    return Pagination(limit=limit, cursor=cursor)
