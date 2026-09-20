import logging
import time

import redis
from fastapi import HTTPException, Request, Response
from jose import JWTError

from app.core.cache import _get_client
from app.core.config import settings
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Extract client IP address, respecting Traefik / proxy X-Forwarded-For headers."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # First IP in X-Forwarded-For is the original client IP
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_client_identifier(request: Request, key_type: str = "ip") -> str:
    """Determine client rate limit bucket key (IP address or authenticated user ID)."""
    if key_type == "user":
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            try:
                payload = decode_access_token(token)
                sub = payload.get("sub")
                if sub:
                    return f"user:{sub}"
            except (JWTError, ValueError) as exc:
                logger.debug("Không parse được token cho rate limiter: %s", exc)
    return f"ip:{get_client_ip(request)}"


class RateLimiter:
    """FastAPI dependency for Redis-backed rate limiting with fail-open resilience."""

    def __init__(
        self,
        times: int | None = None,
        seconds: int = 60,
        scope: str = "default",
        key_type: str = "ip",
        client: redis.Redis | None = None,
    ):
        self.times = times
        self.seconds = seconds
        self.scope = scope
        self.key_type = key_type
        self.client = client

    def _resolve_limit(self) -> int:
        if self.times is not None:
            return self.times
        if self.scope == "login":
            return settings.rate_limit_login_per_minute
        if self.scope in ("ai", "questions", "aggregation", "transcripts"):
            return settings.rate_limit_ai_per_minute
        return 60

    async def __call__(self, request: Request, response: Response) -> None:
        if not settings.rate_limit_enabled:
            return

        client = self.client if self.client is not None else _get_client()
        if client is None:
            # Storage is unreachable - fail open to avoid disrupting active sessions
            logger.warning("Redis không khả dụng cho rate limit - cho phép request đi qua (fail-open).")
            return

        limit = self._resolve_limit()
        now = int(time.time())
        window_id = now // self.seconds
        reset_time = (window_id + 1) * self.seconds
        retry_after = max(1, reset_time - now)

        identifier = get_client_identifier(request, self.key_type)
        redis_key = f"ratelimit:{self.scope}:{identifier}:{window_id}"

        try:
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, self.seconds + 5)
            results = pipe.execute()
            current_count = int(results[0])
        except Exception as e:  # noqa: BLE001 - chủ đích bắt rộng để fail-open tuyệt đối
            # Catch all connection/redis exceptions to fail-open
            logger.warning(
                f"Lỗi kiểm tra rate limit trên Redis key={redis_key}: {e} - cho phép request (fail-open)."
            )
            return

        remaining = max(0, limit - current_count)

        if current_count > limit:
            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(retry_after),
            }
            logger.warning(
                f"Rate limit vượt ngưỡng: scope={self.scope} identifier={identifier} "
                f"count={current_count}/{limit} retry_after={retry_after}s"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers=headers,
            )

        # Attach rate-limit tracking headers to successful response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
