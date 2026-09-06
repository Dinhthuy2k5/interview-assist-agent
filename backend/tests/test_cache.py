from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.competency import FRAMEWORKS_LIST_CACHE_KEY
from app.api.competency import router as competency_router
from app.core.cache import get_cached, set_cached
from app.core.db import get_db
from app.models import Base

app = FastAPI()
app.include_router(competency_router)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    def ping(self):
        return True

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


@pytest.fixture()
def fake_redis():
    instance = FakeRedis()
    with patch("app.core.cache._get_client", return_value=instance):
        yield instance


def test_cache_miss_then_hit(fake_redis):
    assert get_cached("k1") is None
    set_cached("k1", {"a": 1}, ttl_seconds=60)
    assert get_cached("k1") == {"a": 1}


def test_list_frameworks_populates_cache(client, fake_redis):
    client.post("/frameworks", json={"name": "FW1", "criteria": []})

    assert fake_redis.store == {}
    response = client.get("/frameworks")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert FRAMEWORKS_LIST_CACHE_KEY in fake_redis.store


def test_list_frameworks_second_call_hits_cache_not_db(client, fake_redis, db_session):
    client.post("/frameworks", json={"name": "FW1", "criteria": []})
    client.get("/frameworks")

    from app.models.competency import CompetencyFramework

    db_session.query(CompetencyFramework).delete()
    db_session.commit()

    response = client.get("/frameworks")
    assert len(response.json()) == 1


def test_create_framework_invalidates_cache(client, fake_redis):
    client.get("/frameworks")
    assert FRAMEWORKS_LIST_CACHE_KEY in fake_redis.store

    client.post("/frameworks", json={"name": "FW mới", "criteria": []})
    assert FRAMEWORKS_LIST_CACHE_KEY not in fake_redis.store

    response = client.get("/frameworks")
    assert len(response.json()) == 1


def test_update_framework_invalidates_cache(client, fake_redis):
    created = client.post("/frameworks", json={"name": "Old", "criteria": []}).json()
    client.get("/frameworks")
    assert FRAMEWORKS_LIST_CACHE_KEY in fake_redis.store

    client.patch(f"/frameworks/{created['id']}", json={"name": "New"})
    assert FRAMEWORKS_LIST_CACHE_KEY not in fake_redis.store

    response = client.get("/frameworks")
    assert response.json()[0]["name"] == "New"


def test_delete_framework_invalidates_cache(client, fake_redis):
    created = client.post("/frameworks", json={"name": "To delete", "criteria": []}).json()
    client.get("/frameworks")
    assert FRAMEWORKS_LIST_CACHE_KEY in fake_redis.store

    client.delete(f"/frameworks/{created['id']}")
    assert FRAMEWORKS_LIST_CACHE_KEY not in fake_redis.store


def test_app_works_when_redis_completely_unavailable(client, db_session):
    import app.core.cache as cache_module

    cache_module._client = None
    cache_module._connection_failed = False

    with patch("redis.from_url", side_effect=Exception("connection refused")):
        response = client.post("/frameworks", json={"name": "FW1", "criteria": []})
        assert response.status_code == 201

        list_response = client.get("/frameworks")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

    cache_module._client = None
    cache_module._connection_failed = False