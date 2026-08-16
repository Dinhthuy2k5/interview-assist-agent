import uuid
from datetime import UTC, datetime, timedelta

from app.models.competency import CompetencyFramework, Criterion
from app.models.job import Job
from app.models.question import Question


def _make_job_with_approved_question(db_session):
    """Tạo trực tiếp qua ORM (không qua API) - test này tập trung vào logic
    session/note, không phải luồng upload JD/sinh câu hỏi (đã test riêng ở
    test_questions_api.py)."""
    framework = CompetencyFramework(name="Backend", description=None)
    criterion = Criterion(
        name="Problem Solving",
        weight=1.0,
        scoring_rubric="1: Không xác định được vấn đề. 5: Tự giải quyết vấn đề phức tạp.",
    )
    framework.criteria = [criterion]
    db_session.add(framework)
    db_session.flush()

    job = Job(
        title="Backend Dev",
        level="junior",
        jd_file_path="jd/fake.docx",
        jd_text="JD dùng Kafka.",
        jd_parse_status="parsed",
        framework_id=framework.id,
        created_by="HR Admin",
    )
    db_session.add(job)
    db_session.flush()

    approved_question = Question(
        job_id=job.id,
        criterion_id=criterion.id,
        content="Bạn từng debug race condition trong hệ thống Kafka như thế nào?",
        rationale="Đo problem solving",
        generated_by="agent",
        is_approved=True,
    )
    unapproved_question = Question(
        job_id=job.id,
        criterion_id=criterion.id,
        content="Câu hỏi chưa duyệt - không được lộ ra",
        rationale="...",
        generated_by="agent",
        is_approved=False,
    )
    db_session.add_all([approved_question, unapproved_question])
    db_session.commit()

    return job, criterion


def _create_session(client, users, db_session, interviewer_keys=("interviewer1",)):
    job, criterion = _make_job_with_approved_question(db_session)
    payload = {
        "job_id": str(job.id),
        "candidate_name": "Nguyễn Văn A",
        "candidate_info": "5 năm kinh nghiệm",
        "scheduled_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "interviewer_ids": [str(users[k].id) for k in interviewer_keys],
    }
    response = client.post("/sessions", json=payload)
    assert response.status_code == 201, response.text
    return response.json(), job, criterion


def test_create_session_success(client, users, db_session):
    session, _, _ = _create_session(client, users, db_session)
    assert session["status"] == "scheduled"
    assert session["candidate_name"] == "Nguyễn Văn A"


def test_create_session_rejects_non_interviewer_id(client, users, db_session):
    job, _ = _make_job_with_approved_question(db_session)
    payload = {
        "job_id": str(job.id),
        "candidate_name": "B",
        "scheduled_at": datetime.now(UTC).isoformat(),
        # hr_admin không phải role interviewer -> phải bị từ chối
        "interviewer_ids": [str(users["hr_admin"].id)],
    }
    response = client.post("/sessions", json=payload)
    assert response.status_code == 400


def test_create_session_rejects_nonexistent_interviewer_id(client, users, db_session):
    job, _ = _make_job_with_approved_question(db_session)
    payload = {
        "job_id": str(job.id),
        "candidate_name": "B",
        "scheduled_at": datetime.now(UTC).isoformat(),
        "interviewer_ids": [str(uuid.uuid4())],
    }
    response = client.post("/sessions", json=payload)
    assert response.status_code == 400


def test_interviewer_cannot_create_session(client, users, db_session):
    job, _ = _make_job_with_approved_question(db_session)
    payload = {
        "job_id": str(job.id),
        "candidate_name": "B",
        "scheduled_at": datetime.now(UTC).isoformat(),
        "interviewer_ids": [str(users["interviewer1"].id)],
    }
    response = client.as_user(users["interviewer1"]).post("/sessions", json=payload)
    assert response.status_code == 403


def test_list_my_sessions_only_shows_assigned(client, users, db_session):
    session, _, _ = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))

    mine = client.as_user(users["interviewer1"]).get("/sessions/mine")
    assert mine.status_code == 200
    assert len(mine.json()) == 1
    assert mine.json()[0]["id"] == session["id"]

    other = client.as_user(users["interviewer2"]).get("/sessions/mine")
    assert other.status_code == 200
    assert other.json() == []


def test_participant_can_view_session_detail_with_rubric(client, users, db_session):
    session, _, criterion = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))

    response = client.as_user(users["interviewer1"]).get(f"/sessions/{session['id']}")
    assert response.status_code == 200
    body = response.json()

    # Chỉ câu đã duyệt được trả về (unapproved_question phải bị lọc).
    assert len(body["questions"]) == 1
    q = body["questions"][0]
    assert q["criterion_id"] == str(criterion.id)
    assert q["criterion_name"] == "Problem Solving"
    assert "5: Tự giải quyết" in q["scoring_rubric"]
    assert body["my_notes"] == []


def test_non_participant_interviewer_forbidden(client, users, db_session):
    session, _, _ = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))

    response = client.as_user(users["interviewer2"]).get(f"/sessions/{session['id']}")
    assert response.status_code == 403


def test_council_forbidden_from_session_detail(client, users, db_session):
    """Regression test cho lỗ hổng đã sửa: trước đây mọi role khác interviewer
    đều lọt qua không kiểm tra, kể cả council."""
    session, _, _ = _create_session(client, users, db_session)

    response = client.as_user(users["council"]).get(f"/sessions/{session['id']}")
    assert response.status_code == 403


def test_hr_admin_can_view_any_session(client, users, db_session):
    session, _, _ = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))

    # client mặc định đã là hr_admin, không cần as_user
    response = client.get(f"/sessions/{session['id']}")
    assert response.status_code == 200


def test_upsert_note_creates_then_updates_not_duplicates(client, users, db_session):
    session, _, criterion = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))
    interviewer_client = client.as_user(users["interviewer1"])

    first = interviewer_client.put(
        f"/sessions/{session['id']}/notes/{criterion.id}",
        json={"score": 3, "note_text": "Ổn"},
    )
    assert first.status_code == 200
    assert first.json()["score"] == 3

    second = interviewer_client.put(
        f"/sessions/{session['id']}/notes/{criterion.id}",
        json={"score": 5, "note_text": "Xuất sắc, đổi ý sau khi hỏi thêm"},
    )
    assert second.status_code == 200
    assert second.json()["score"] == 5
    assert second.json()["id"] == first.json()["id"]  # cùng 1 bản ghi, không tạo mới

    detail = interviewer_client.get(f"/sessions/{session['id']}")
    assert len(detail.json()["my_notes"]) == 1
    assert detail.json()["my_notes"][0]["score"] == 5


def test_non_participant_cannot_write_note(client, users, db_session):
    session, _, criterion = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))

    response = client.as_user(users["interviewer2"]).put(
        f"/sessions/{session['id']}/notes/{criterion.id}",
        json={"score": 4, "note_text": "Không được phép"},
    )
    assert response.status_code == 403


def test_notes_isolated_between_interviewers(client, users, db_session):
    """Đúng nguyên tắc công bằng: 2 interviewer cùng session, mỗi người chỉ thấy
    note của chính mình, không thấy note người kia dù cùng criterion."""
    session, _, criterion = _create_session(
        client, users, db_session, interviewer_keys=("interviewer1", "interviewer2")
    )

    client.as_user(users["interviewer1"]).put(
        f"/sessions/{session['id']}/notes/{criterion.id}",
        json={"score": 2, "note_text": "Note của interviewer 1"},
    )
    client.as_user(users["interviewer2"]).put(
        f"/sessions/{session['id']}/notes/{criterion.id}",
        json={"score": 5, "note_text": "Note của interviewer 2"},
    )

    detail1 = client.as_user(users["interviewer1"]).get(f"/sessions/{session['id']}")
    assert len(detail1.json()["my_notes"]) == 1
    assert detail1.json()["my_notes"][0]["score"] == 2

    detail2 = client.as_user(users["interviewer2"]).get(f"/sessions/{session['id']}")
    assert len(detail2.json()["my_notes"]) == 1
    assert detail2.json()["my_notes"][0]["score"] == 5


def test_update_status_by_participant_and_hr(client, users, db_session):
    session, _, _ = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))

    resp = client.as_user(users["interviewer1"]).patch(
        f"/sessions/{session['id']}/status", json={"status": "in_progress"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    resp2 = client.patch(f"/sessions/{session['id']}/status", json={"status": "completed"})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "completed"


def test_update_status_rejected_for_non_participant(client, users, db_session):
    session, _, _ = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))

    response = client.as_user(users["interviewer2"]).patch(
        f"/sessions/{session['id']}/status", json={"status": "completed"}
    )
    assert response.status_code == 403


def test_update_status_rejects_invalid_value(client, users, db_session):
    session, _, _ = _create_session(client, users, db_session)
    response = client.patch(f"/sessions/{session['id']}/status", json={"status": "huy_bo"})
    assert response.status_code == 422  # Literal type tự validate ở tầng schema


def test_list_sessions_hr_only_and_filter_by_job(client, users, db_session):
    session1, job1, _ = _create_session(client, users, db_session)
    _session2, _job2, _ = _create_session(client, users, db_session)

    all_sessions = client.get("/sessions")
    assert all_sessions.status_code == 200
    assert len(all_sessions.json()) == 2

    filtered = client.get(f"/sessions?job_id={job1.id}")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["id"] == session1["id"]

    forbidden = client.as_user(users["interviewer1"]).get("/sessions")
    assert forbidden.status_code == 403