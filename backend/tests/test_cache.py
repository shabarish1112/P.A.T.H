from __future__ import annotations

import time

from app.core.cache import MemoryCache, cache_miss


def test_cache_ttl_and_invalidation() -> None:
    cache = MemoryCache()
    cache.set('analytics:x', {'ok': True}, 1)
    assert cache.get('analytics:x') == {'ok': True}
    cache.invalidate('analytics:')
    assert cache.get('analytics:x') is cache_miss()
    cache.set('x', 1, 1)
    time.sleep(1.01)
    assert cache.get('x') is cache_miss()
