import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.models.competency import CompetencyFramework, Criterion
from app.models.job import Job
from app.models.session import InterviewerNote
from app.services.aggregation import build_interviewer_labels


def test_build_interviewer_labels_stable_and_order_preserving():
    """Unit test thuần - đúng phần logic bị bug trước đây (label gán lại theo từng
    criterion). Không đụng DB nên không phụ thuộc thứ tự query trả về."""
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    labels = build_interviewer_labels([a, b, c])

    assert labels[a] == "Người phỏng vấn 1"
    assert labels[b] == "Người phỏng vấn 2"
    assert labels[c] == "Người phỏng vấn 3"

    # Gọi lại với đúng thứ tự input y hệt -> kết quả giống hệt (ổn định).
    assert build_interviewer_labels([a, b, c]) == labels


def _create_session_with_two_criteria(client, users, db_session, interviewer_keys=("interviewer1", "interviewer2")):
    framework = CompetencyFramework(name="Backend", description=None)
    c1 = Criterion(name="Problem Solving", weight=1.0, scoring_rubric="1-5")
    c2 = Criterion(name="System Design", weight=1.0, scoring_rubric="1-5")
    framework.criteria = [c1, c2]
    db_session.add(framework)
    db_session.flush()

    job = Job(
        title="Backend Dev",
        level="junior",
        jd_file_path="jd/fake.docx",
        jd_text="JD",
        jd_parse_status="parsed",
        framework_id=framework.id,
        created_by="HR Admin",
    )
    db_session.add(job)
    db_session.flush()

    payload = {
        "job_id": str(job.id),
        "candidate_name": "Nguyễn Văn A",
        "scheduled_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "interviewer_ids": [str(users[k].id) for k in interviewer_keys],
    }
    response = client.post("/sessions", json=payload)
    assert response.status_code == 201, response.text
    return response.json(), c1, c2


def _add_note(db_session, session_id, interviewer_id, criterion_id, score, note_text):
    db_session.add(
        InterviewerNote(
            session_id=uuid.UUID(session_id),
            interviewer_id=interviewer_id,
            criterion_id=criterion_id,
            score=score,
            note_text=note_text,
        )
    )
    db_session.commit()


def test_aggregate_forbidden_for_interviewer_and_council(client, users, db_session):
    session, _, _ = _create_session_with_two_criteria(client, users, db_session)

    for role_key in ("interviewer1", "council"):
        response = client.as_user(users[role_key]).post(f"/sessions/{session['id']}/aggregate")
        assert response.status_code == 403


def test_get_aggregation_allowed_for_hr_and_council_forbidden_for_interviewer(client, users, db_session):
    session, c1, c2 = _create_session_with_two_criteria(client, users, db_session)
    _add_note(db_session, session["id"], users["interviewer1"].id, c1.id, 3, "ổn")

    client.post(f"/sessions/{session['id']}/aggregate")

    assert client.get(f"/sessions/{session['id']}/aggregation").status_code == 200
    assert client.as_user(users["council"]).get(f"/sessions/{session['id']}/aggregation").status_code == 200
    assert (
        client.as_user(users["interviewer1"]).get(f"/sessions/{session['id']}/aggregation").status_code
        == 403
    )


def test_get_aggregation_before_aggregate_returns_404(client, users, db_session):
    session, _, _ = _create_session_with_two_criteria(client, users, db_session)
    response = client.get(f"/sessions/{session['id']}/aggregation")
    assert response.status_code == 404


def test_rule_based_conflict_detected_and_uses_mock_summary(client, users, db_session):
    """settings.llm_provider mặc định "mock" trong test (config.py) - verify không
    gọi LLM thật, summary bắt đầu bằng [MOCK]."""
    session, c1, c2 = _create_session_with_two_criteria(client, users, db_session)
    _add_note(db_session, session["id"], users["interviewer1"].id, c1.id, 1, "Không xác định được vấn đề")
    _add_note(db_session, session["id"], users["interviewer2"].id, c1.id, 5, "Xử lý xuất sắc")

    response = client.post(f"/sessions/{session['id']}/aggregate")
    assert response.status_code == 200

    summaries = {s["criterion_id"]: s for s in response.json()["per_criterion_summary"]}
    c1_summary = summaries[str(c1.id)]
    assert c1_summary["has_conflict"] is True
    assert c1_summary["conflict_type"] == "rule_based"
    assert c1_summary["semantic_note"].startswith("[MOCK]")


def test_no_conflict_when_scores_close_and_notes_similar(client, users, db_session):
    session, c1, c2 = _create_session_with_two_criteria(client, users, db_session)
    _add_note(db_session, session["id"], users["interviewer1"].id, c1.id, 4, "Xử lý tốt")
    _add_note(db_session, session["id"], users["interviewer2"].id, c1.id, 4, "Xử lý tốt")

    with patch("app.services.aggregation.compute_similarity", return_value=0.95):
        response = client.post(f"/sessions/{session['id']}/aggregate")

    summaries = {s["criterion_id"]: s for s in response.json()["per_criterion_summary"]}
    assert summaries[str(c1.id)]["has_conflict"] is False


def test_embedding_conflict_detected_when_scores_close_but_notes_differ(client, users, db_session):
    session, c1, c2 = _create_session_with_two_criteria(client, users, db_session)
    _add_note(db_session, session["id"], users["interviewer1"].id, c1.id, 3, "Chỉ nêu được hướng chung")
    _add_note(db_session, session["id"], users["interviewer2"].id, c1.id, 3, "Giải quyết triệt để vấn đề")

    with patch("app.services.aggregation.compute_similarity", return_value=0.2):
        response = client.post(f"/sessions/{session['id']}/aggregate")

    summaries = {s["criterion_id"]: s for s in response.json()["per_criterion_summary"]}
    assert summaries[str(c1.id)]["has_conflict"] is True
    assert summaries[str(c1.id)]["conflict_type"] == "embedding"


def test_missing_interviewer_labels_reported_per_criterion(client, users, db_session):
    session, c1, c2 = _create_session_with_two_criteria(client, users, db_session)
    _add_note(db_session, session["id"], users["interviewer1"].id, c1.id, 3, "ổn")
    _add_note(db_session, session["id"], users["interviewer2"].id, c1.id, 3, "ổn")
    # Chỉ interviewer1 note criterion 2 - interviewer2 thiếu ở đây.
    _add_note(db_session, session["id"], users["interviewer1"].id, c2.id, 4, "tốt")

    response = client.post(f"/sessions/{session['id']}/aggregate")
    summaries = {s["criterion_id"]: s for s in response.json()["per_criterion_summary"]}

    assert summaries[str(c1.id)]["missing_interviewer_labels"] == []
    assert len(summaries[str(c2.id)]["missing_interviewer_labels"]) == 1


def test_aggregate_without_any_note_returns_no_data_recommendation(client, users, db_session):
    session, _, _ = _create_session_with_two_criteria(client, users, db_session)
    response = client.post(f"/sessions/{session['id']}/aggregate")

    assert response.status_code == 200
    body = response.json()
    assert body["overall_score"] is None
    assert body["overall_recommendation"] == "Chưa đủ dữ liệu"


def test_aggregate_twice_upserts_not_duplicates(client, users, db_session):
    session, c1, _ = _create_session_with_two_criteria(client, users, db_session)
    _add_note(db_session, session["id"], users["interviewer1"].id, c1.id, 3, "ổn")

    first = client.post(f"/sessions/{session['id']}/aggregate")
    second = client.post(f"/sessions/{session['id']}/aggregate")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]  # cùng 1 bản ghi, upsert không tạo mới


def test_aggregate_without_interviewers_returns_400(client, users, db_session):
    framework = CompetencyFramework(name="Backend", description=None)
    framework.criteria = [Criterion(name="X", weight=1.0, scoring_rubric="1-5")]
    db_session.add(framework)
    db_session.flush()

    job = Job(
        title="Backend Dev",
        level="junior",
        jd_file_path="jd/fake.docx",
        jd_text="JD",
        jd_parse_status="parsed",
        framework_id=framework.id,
        created_by="HR Admin",
    )
    db_session.add(job)
    db_session.commit()

    # Tạo session thẳng qua model để bypass validate interviewer_ids bắt buộc >=1
    # của SessionCreate - test riêng nhánh "session tồn tại nhưng 0 interviewer".
    from app.models.session import InterviewSession

    session = InterviewSession(
        job_id=job.id,
        candidate_name="B",
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
    )
    db_session.add(session)
    db_session.commit()

    response = client.post(f"/sessions/{session.id}/aggregate")
    assert response.status_code == 400