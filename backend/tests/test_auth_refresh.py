import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.core.security import hash_password
from app.main import app
from app.models import Base, User
from app.models.user import UserRole


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


@pytest.fixture()
def user(db_session):
    u = User(
        email="hr@test.local",
        full_name="HR Test",
        password_hash=hash_password("correct-password"),
        role=UserRole.hr_admin.value,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def test_login_returns_both_tokens(client, user):
    response = client.post(
        "/auth/login", data={"username": "hr@test.local", "password": "correct-password"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, user):
    response = client.post("/auth/login", data={"username": "hr@test.local", "password": "sai"})
    assert response.status_code == 401


def test_refresh_issues_new_pair_and_revokes_old(client, user):
    login = client.post(
        "/auth/login", data={"username": "hr@test.local", "password": "correct-password"}
    ).json()

    refresh_response = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()

    assert new_tokens["access_token"] != login["access_token"]
    assert new_tokens["refresh_token"] != login["refresh_token"]


def test_reusing_old_refresh_token_after_rotation_fails(client, user):
    """Đúng cơ chế rotation: dùng lại refresh_token CŨ sau khi đã rotate 1 lần
    phải bị từ chối."""
    login = client.post(
        "/auth/login", data={"username": "hr@test.local", "password": "correct-password"}
    ).json()

    client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})

    reuse_response = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert reuse_response.status_code == 401


def test_reuse_detection_revokes_all_tokens_of_user(client, user):
    """Phát hiện dùng lại token cũ -> revoke TOÀN BỘ refresh token còn sống của
    user, không chỉ mỗi token bị dùng lại - buộc đăng nhập lại mọi nơi."""
    login = client.post(
        "/auth/login", data={"username": "hr@test.local", "password": "correct-password"}
    ).json()
    rotated = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]}).json()

    # Dùng lại token cũ (đã bị revoke) -> kích hoạt revoke toàn bộ
    client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})

    # Token MỚI (rotated) vừa cấp hợp lệ trước đó giờ cũng phải bị revoke theo
    still_valid = client.post("/auth/refresh", json={"refresh_token": rotated["refresh_token"]})
    assert still_valid.status_code == 401


def test_logout_revokes_refresh_token(client, user):
    login = client.post(
        "/auth/login", data={"username": "hr@test.local", "password": "correct-password"}
    ).json()

    logout_response = client.post("/auth/logout", json={"refresh_token": login["refresh_token"]})
    assert logout_response.status_code == 204

    refresh_after_logout = client.post(
        "/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert refresh_after_logout.status_code == 401


def test_logout_is_idempotent(client, user):
    login = client.post(
        "/auth/login", data={"username": "hr@test.local", "password": "correct-password"}
    ).json()

    first = client.post("/auth/logout", json={"refresh_token": login["refresh_token"]})
    second = client.post("/auth/logout", json={"refresh_token": login["refresh_token"]})
    assert first.status_code == 204
    assert second.status_code == 204


def test_refresh_with_garbage_token_returns_401(client, user):
    response = client.post("/auth/refresh", json={"refresh_token": "khong-ton-tai"})
    assert response.status_code == 401


def test_me_endpoint_works_with_issued_access_token(client, user):
    login = client.post(
        "/auth/login", data={"username": "hr@test.local", "password": "correct-password"}
    ).json()

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert response.status_code == 200
    assert response.json()["email"] == "hr@test.local"