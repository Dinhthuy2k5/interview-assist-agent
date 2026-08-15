import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.core.db import get_db
from app.main import app
from app.models import Base
from app.models.user import User, UserRole


@pytest.fixture()
def db_session():
    """DB SQLite in-memory riêng cho mỗi test — tạo bảng mới, xoá sạch sau khi xong.
    StaticPool để toàn bộ test dùng chung 1 connection (SQLite in-memory mất data
    nếu mỗi request mở connection mới)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def _fake_hr_admin() -> User:
    """User giả, không lưu DB - chỉ cần đủ attribute mà endpoint dùng tới
    (role để qua require_role, full_name vì jobs.py lấy created_by từ đây).
    Test hiện tại đều mô phỏng hành vi của HR Admin nên fix cứng role này;
    nếu sau này có test riêng cho Interviewer/Council, override lại
    get_current_user trong từng test đó thay vì sửa fixture chung."""
    return User(
        id=uuid.uuid4(),
        email="hr_test@example.com",
        full_name="HR Test",
        password_hash="unused-in-tests",
        role=UserRole.hr_admin.value,
        is_active=True,
    )


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return _fake_hr_admin()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()