import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

from app.config import settings

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()
_MAX_TRACKED_CLIENTS = 10_000

def reset() -> None:
    with _lock:
        _hits.clear()

def client_ip(request: Request) -> str:
    """
    На Render клиентский IP приходит в True-Client-IP, его выставляет Cloudflare
    X-Forwarded-For не используй, клиент может подделать его
    """
    return (
        request.headers.get("true-client-ip")
        or request.headers.get("cf-connecting-ip")
        or (request.client.host if request.client else "unknown")
    )

def rate_limit_create(request: Request) -> None:
    """
    Скользящее окно: не больше create_rate_limit запросов за create_rate_window секунд на IP
    """
    limit = settings.create_rate_limit
    window = settings.create_rate_window
    if limit <= 0:
        return

    now = time.monotonic()
    ip = client_ip(request)

    with _lock:
        if len(_hits) > _MAX_TRACKED_CLIENTS:
            for key in [k for k, v in _hits.items() if not v or now - v[-1] > window]:
                del _hits[key]

        hits = _hits[ip]
        while hits and now - hits[0] > window:
            hits.popleft()

        if len(hits) >= limit:
            retry_after = int(window - (now - hits[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Try again later",
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)