from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.models.competency import CompetencyFramework
from app.models.job import Job
from app.services.stt import TranscriptionError


def _create_session(client, users, db_session, interviewer_keys=("interviewer1",)):
    framework = CompetencyFramework(name="Backend", description=None)
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
    db_session.commit()

    payload = {
        "job_id": str(job.id),
        "candidate_name": "Nguyễn Văn A",
        "scheduled_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "interviewer_ids": [str(users[k].id) for k in interviewer_keys],
    }
    response = client.post("/sessions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _fake_audio_file():
    return {"file": ("interview.mp3", b"fake audio bytes", "audio/mpeg")}


def test_hr_admin_can_upload_and_transcript_completed(client, users, db_session):
    session = _create_session(client, users, db_session)
    with (
        patch("app.api.transcripts.upload_file", return_value="audio/fake.mp3"),
        patch("app.api.transcripts.transcribe_audio", return_value="Xin chào, bắt đầu phỏng vấn."),
    ):
        response = client.post(f"/sessions/{session['id']}/transcript", files=_fake_audio_file())

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["text"] == "Xin chào, bắt đầu phỏng vấn."
    assert "audio_file_path" not in body  # không lộ object key nội bộ MinIO


def test_participant_interviewer_can_upload(client, users, db_session):
    session = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))
    with (
        patch("app.api.transcripts.upload_file", return_value="audio/fake.mp3"),
        patch("app.api.transcripts.transcribe_audio", return_value="..."),
    ):
        response = client.as_user(users["interviewer1"]).post(
            f"/sessions/{session['id']}/transcript", files=_fake_audio_file()
        )
    assert response.status_code == 201


def test_non_participant_interviewer_forbidden_upload(client, users, db_session):
    session = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))
    response = client.as_user(users["interviewer2"]).post(
        f"/sessions/{session['id']}/transcript", files=_fake_audio_file()
    )
    assert response.status_code == 403


def test_council_forbidden_upload(client, users, db_session):
    """Regression test cùng loại bug đã từng gặp ở get_session_detail: council
    không có use case cho transcript, phải bị chặn tường minh."""
    session = _create_session(client, users, db_session)
    response = client.as_user(users["council"]).post(
        f"/sessions/{session['id']}/transcript", files=_fake_audio_file()
    )
    assert response.status_code == 403


def test_upload_rejects_unsupported_extension(client, users, db_session):
    session = _create_session(client, users, db_session)
    files = {"file": ("notes.txt", b"not audio", "text/plain")}
    response = client.post(f"/sessions/{session['id']}/transcript", files=files)
    assert response.status_code == 400


def test_upload_rejects_oversized_file(client, users, db_session):
    session = _create_session(client, users, db_session)
    with patch("app.api.transcripts.MAX_AUDIO_BYTES", 10):
        files = {"file": ("interview.mp3", b"x" * 100, "audio/mpeg")}
        response = client.post(f"/sessions/{session['id']}/transcript", files=files)
    assert response.status_code == 400


def test_upload_twice_conflicts(client, users, db_session):
    session = _create_session(client, users, db_session)
    with (
        patch("app.api.transcripts.upload_file", return_value="audio/fake.mp3"),
        patch("app.api.transcripts.transcribe_audio", return_value="..."),
    ):
        first = client.post(f"/sessions/{session['id']}/transcript", files=_fake_audio_file())
        assert first.status_code == 201
        second = client.post(f"/sessions/{session['id']}/transcript", files=_fake_audio_file())
    assert second.status_code == 409


def test_transcription_failure_still_saves_record_as_failed(client, users, db_session):
    session = _create_session(client, users, db_session)
    with (
        patch("app.api.transcripts.upload_file", return_value="audio/fake.mp3"),
        patch("app.api.transcripts.transcribe_audio", side_effect=TranscriptionError("model lỗi")),
    ):
        response = client.post(f"/sessions/{session['id']}/transcript", files=_fake_audio_file())

    assert response.status_code == 201  # vẫn tạo record, chỉ đánh dấu failed
    assert response.json()["status"] == "failed"
    assert response.json()["text"] is None


def test_get_transcript_before_upload_returns_404(client, users, db_session):
    session = _create_session(client, users, db_session)
    response = client.get(f"/sessions/{session['id']}/transcript")
    assert response.status_code == 404


def test_get_transcript_permission_matrix(client, users, db_session):
    session = _create_session(client, users, db_session, interviewer_keys=("interviewer1",))
    with (
        patch("app.api.transcripts.upload_file", return_value="audio/fake.mp3"),
        patch("app.api.transcripts.transcribe_audio", return_value="nội dung transcript"),
    ):
        client.post(f"/sessions/{session['id']}/transcript", files=_fake_audio_file())

    # hr_admin (giám sát) - luôn xem được
    assert client.get(f"/sessions/{session['id']}/transcript").status_code == 200

    # interviewer tham gia - xem được
    ok = client.as_user(users["interviewer1"]).get(f"/sessions/{session['id']}/transcript")
    assert ok.status_code == 200
    assert ok.json()["text"] == "nội dung transcript"

    # interviewer không tham gia - bị chặn
    forbidden = client.as_user(users["interviewer2"]).get(f"/sessions/{session['id']}/transcript")
    assert forbidden.status_code == 403

    # council - chưa có use case, bị chặn
    council_forbidden = client.as_user(users["council"]).get(f"/sessions/{session['id']}/transcript")
    assert council_forbidden.status_code == 403