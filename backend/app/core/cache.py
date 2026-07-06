import redis
import json
from app.core.config import settings

if settings.REDIS_URL:
    client = redis.from_url(settings.REDIS_URL)
else:
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )


def get_cached(key: str) -> dict | None:
    """
    Get cached value by key.
    Returns None if not found or expired.
    """
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"[Cache] Get failed: {e}")
        return None


def set_cached(key: str, value: dict, ttl: int = None) -> bool:
    """
    Cache a value with optional TTL.
    Returns True if successful.
    """
    try:
        client.setex(
            name=key,
            time=ttl or settings.CACHE_TTL,
            value=json.dumps(value)
        )
        return True
    except Exception as e:
        print(f"[Cache] Set failed: {e}")
        return False


def invalidate(key: str) -> bool:
    """
    Delete a cached value — use when underlying data changes.
    """
    try:
        client.delete(key)
        return True
    except Exception as e:
        print(f"[Cache] Invalidate failed: {e}")
        return False


def make_job_cache_key(filename: str) -> str:
    """
    Consistent key format for job search results.
    """
    return f"jobs:{filename}"