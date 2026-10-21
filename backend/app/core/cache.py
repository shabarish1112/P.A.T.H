from __future__ import annotations

import json
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

from redis import Redis

from app.core.config import Settings

_MISS = object()


class CacheBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> object:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def invalidate(self, prefix: str = '') -> None:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> object:
        now = time.monotonic()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return _MISS
            expires_at, value = item
            if expires_at <= now:
                self._items.pop(key, None)
                return _MISS
            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._items[key] = (time.monotonic() + ttl_seconds, value)

    def invalidate(self, prefix: str = '') -> None:
        with self._lock:
            if not prefix:
                self._items.clear()
                return
            for key in list(self._items):
                if key.startswith(prefix):
                    self._items.pop(key, None)


class RedisCache(CacheBackend):
    def __init__(self, url: str) -> None:
        self.client = Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> object:
        value = self.client.get(key)
        return _MISS if value is None else json.loads(value)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self.client.setex(key, ttl_seconds, json.dumps(value, default=str))

    def invalidate(self, prefix: str = '') -> None:
        pattern = f'{prefix}*' if prefix else '*'
        keys = list(self.client.scan_iter(pattern))
        if keys:
            self.client.delete(*keys)


_cache: CacheBackend | None = None


def get_cache(settings: Settings) -> CacheBackend:
    global _cache
    if _cache is None:
        if settings.cache_backend == 'redis':
            if not settings.redis_url:
                raise RuntimeError('REDIS_URL is required when CACHE_BACKEND=redis')
            _cache = RedisCache(settings.redis_url)
        else:
            _cache = MemoryCache()
    return _cache


def cache_miss() -> object:
    return _MISS
