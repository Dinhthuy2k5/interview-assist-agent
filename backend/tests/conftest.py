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


def _make_user(role: UserRole, label: str) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{label}@test.com",
        full_name=label,
        password_hash="unused-in-tests",
        role=role.value,
        is_active=True,
    )


@pytest.fixture()
def users(db_session) -> dict[str, User]:
    """User THẬT, có lưu DB - cần thiết cho các test liên quan tới session/note,
    vì create_session validate interviewer_ids bằng cách query DB thật
    (db.get(User, uid)), không chỉ dựa vào danh tính người gọi API.
    Test không liên quan tới session (framework/job/question) không cần fixture
    này, chỉ cần fixture `client` mặc định (đăng nhập sẵn là hr_admin)."""
    pool = {
        "hr_admin": _make_user(UserRole.hr_admin, "HR Admin"),
        "interviewer1": _make_user(UserRole.interviewer, "Interviewer One"),
        "interviewer2": _make_user(UserRole.interviewer, "Interviewer Two"),
        "council": _make_user(UserRole.council, "Council Member"),
    }
    db_session.add_all(pool.values())
    db_session.commit()
    return pool


@pytest.fixture()
def client(db_session, users):
    """Mặc định đăng nhập là hr_admin - giữ tương thích các test cũ (framework,
    job, question) không cần biết về multi-user.

    Dùng client.as_user(users["interviewer1"]) để đổi danh tính đang gọi API
    NGAY TRONG 1 TEST - cần thiết để mô phỏng nhiều actor tương tác trên cùng
    1 session (HR tạo -> interviewer A xem -> interviewer B ghi note...)."""
    current = {"user": users["hr_admin"]}

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return current["user"]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    test_client = TestClient(app)

    def as_user(user: User) -> TestClient:
        current["user"] = user
        return test_client

    test_client.as_user = as_user  # type: ignore[attr-defined]

    with test_client:
        yield test_client
    app.dependency_overrides.clear()