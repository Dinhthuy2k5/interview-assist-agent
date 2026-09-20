from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.core.security import create_access_token


class FakePipeline:
    def __init__(self, store: dict[str, int]):
        self.store = store
        self.commands: list = []

    def incr(self, key: str):
        def cmd():
            val = self.store.get(key, 0) + 1
            self.store[key] = val
            return val

        self.commands.append(cmd)
        return self

    def expire(self, key: str, seconds: int):
        def cmd():
            return True

        self.commands.append(cmd)
        return self

    def execute(self):
        results = [c() for c in self.commands]
        self.commands.clear()
        return results


class FakeRedisForRateLimit:
    def __init__(self):
        self.store: dict[str, int] = {}

    def pipeline(self):
        return FakePipeline(self.store)


@pytest.fixture()
def fake_redis():
    instance = FakeRedisForRateLimit()
    with patch("app.core.rate_limit._get_client", return_value=instance):
        yield instance


def create_test_app():
    app = FastAPI()

    # Route with IP rate limit: 3 requests per 60 seconds
    @app.post("/test-ip", dependencies=[Depends(RateLimiter(times=3, seconds=60, scope="test_ip"))])
    def test_ip_endpoint():
        return {"status": "ok"}

    # Route with User rate limit: 2 requests per 60 seconds
    @app.post(
        "/test-user",
        dependencies=[Depends(RateLimiter(times=2, seconds=60, scope="test_user", key_type="user"))],
    )
    def test_user_endpoint():
        return {"status": "ok"}

    return app


def test_ip_rate_limiting_allows_within_limit_and_attaches_headers(fake_redis):
    app = create_test_app()
    client = TestClient(app)

    for i in range(1, 4):
        res = client.post("/test-ip")
        assert res.status_code == 200
        assert res.headers["X-RateLimit-Limit"] == "3"
        assert res.headers["X-RateLimit-Remaining"] == str(3 - i)
        assert "X-RateLimit-Reset" in res.headers


def test_ip_rate_limiting_blocks_when_limit_exceeded(fake_redis):
    app = create_test_app()
    client = TestClient(app)

    # 3 allowed requests
    for _ in range(3):
        res = client.post("/test-ip")
        assert res.status_code == 200

    # 4th request must be rejected with 429
    res = client.post("/test-ip")
    assert res.status_code == 429
    assert res.headers["X-RateLimit-Limit"] == "3"
    assert res.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in res.headers
    assert int(res.headers["Retry-After"]) >= 1
    assert "Rate limit exceeded" in res.json()["detail"]


def test_rate_limiting_respects_x_forwarded_for_header(fake_redis):
    app = create_test_app()
    client = TestClient(app)

    # IP 1 uses all 3 quota requests
    for _ in range(3):
        res = client.post("/test-ip", headers={"X-Forwarded-For": "203.0.113.195, 10.0.0.1"})
        assert res.status_code == 200

    # IP 1 gets blocked
    res_blocked = client.post("/test-ip", headers={"X-Forwarded-For": "203.0.113.195, 10.0.0.1"})
    assert res_blocked.status_code == 429

    # IP 2 still has full quota
    res_other = client.post("/test-ip", headers={"X-Forwarded-For": "198.51.100.42"})
    assert res_other.status_code == 200
    assert res_other.headers["X-RateLimit-Remaining"] == "2"


def test_user_rate_limiting_distinguishes_users_by_token(fake_redis):
    app = create_test_app()
    client = TestClient(app)

    token_user_1 = create_access_token("user-111", "interviewer")
    token_user_2 = create_access_token("user-222", "interviewer")

    # User 1 uses 2 requests
    for _ in range(2):
        res = client.post("/test-user", headers={"Authorization": f"Bearer {token_user_1}"})
        assert res.status_code == 200

    # User 1 3rd request is blocked
    res_user1_blocked = client.post(
        "/test-user", headers={"Authorization": f"Bearer {token_user_1}"}
    )
    assert res_user1_blocked.status_code == 429

    # User 2 is not affected by User 1's quota exhaustion
    res_user2 = client.post("/test-user", headers={"Authorization": f"Bearer {token_user_2}"})
    assert res_user2.status_code == 200
    assert res_user2.headers["X-RateLimit-Remaining"] == "1"


def test_rate_limiter_fails_open_when_redis_unavailable():
    app = create_test_app()
    client = TestClient(app)

    # Mock _get_client returning None (Redis completely unreachable)
    with patch("app.core.rate_limit._get_client", return_value=None):
        for _ in range(10):
            res = client.post("/test-ip")
            assert res.status_code == 200
            assert res.json() == {"status": "ok"}


def test_rate_limiter_fails_open_when_redis_raises_exception():
    app = create_test_app()
    client = TestClient(app)

    class BrokenRedis:
        def pipeline(self):
            raise ConnectionError("Redis cluster unreachable")

    with patch("app.core.rate_limit._get_client", return_value=BrokenRedis()):
        res = client.post("/test-ip")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


def test_rate_limiting_bypassed_when_disabled(fake_redis):
    app = create_test_app()
    client = TestClient(app)

    with patch.object(settings, "rate_limit_enabled", False):
        # Even after 10 requests, should not be blocked
        for _ in range(10):
            res = client.post("/test-ip")
            assert res.status_code == 200
