from unittest.mock import patch

from app.services.question_gen import QuestionGenError


def _create_framework_and_job(client, jd_text="JD dùng Kafka và microservices."):
    framework = client.post(
        "/frameworks",
        json={
            "name": "Backend",
            "criteria": [
                {"name": "Problem Solving", "weight": 1.0, "scoring_rubric": "1-5"},
                {"name": "Communication", "weight": 1.0, "scoring_rubric": "1-5"},
            ],
        },
    ).json()

    files = {"file": ("jd.docx", b"fake docx bytes", "application/octet-stream")}
    data = {
        "title": "Backend Dev",
        "level": "junior",
        "framework_id": framework["id"],
        "created_by": "hr_test",
    }
    with patch("app.api.jobs.upload_file", return_value="jd/fake.docx"), patch(
        "app.api.jobs.parse_jd_file", return_value=(jd_text, "parsed")
    ):
        job = client.post("/jobs", files=files, data=data).json()
    return framework, job


def test_generate_questions_creates_one_per_criterion(client):
    framework, job = _create_framework_and_job(client)

    mock_data = ({"question": "Câu hỏi mẫu?", "rationale": "Đo problem solving"}, {
        "tokens_in": 100,
        "tokens_out": 50,
        "cost_estimate": 0.001,
    })
    with patch("app.api.questions.generate_question_for_criterion", return_value=mock_data):
        response = client.post(f"/jobs/{job['id']}/questions/generate")

    assert response.status_code == 200
    questions = response.json()
    assert len(questions) == len(framework["criteria"])
    assert all(q["is_approved"] is False for q in questions)
    assert all(q["generated_by"] == "agent" for q in questions)


def test_generate_questions_flags_sensitive_content(client):
    _, job = _create_framework_and_job(client)

    mock_data = ({"question": "Bạn đã kết hôn chưa?", "rationale": "..."}, {
        "tokens_in": 10,
        "tokens_out": 10,
        "cost_estimate": 0.0001,
    })
    with patch("app.api.questions.generate_question_for_criterion", return_value=mock_data):
        response = client.post(f"/jobs/{job['id']}/questions/generate")

    questions = response.json()
    assert all(q["is_sensitive_flagged"] is True for q in questions)

    list_response = client.get(f"/jobs/{job['id']}/questions")
    assert list_response.json() == []


def test_generate_questions_without_jd_text_returns_400(client):
    _, job = _create_framework_and_job(client, jd_text="")
    response = client.post(f"/jobs/{job['id']}/questions/generate")
    assert response.status_code == 400


def test_generate_questions_propagates_llm_error_as_502(client):
    _, job = _create_framework_and_job(client)
    with patch(
        "app.api.questions.generate_question_for_criterion",
        side_effect=QuestionGenError("bad json"),
    ):
        response = client.post(f"/jobs/{job['id']}/questions/generate")
    assert response.status_code == 502


def test_update_question_approve_and_edit(client):
    _, job = _create_framework_and_job(client)
    mock_data = ({"question": "Q?", "rationale": "R"}, {
        "tokens_in": 5,
        "tokens_out": 5,
        "cost_estimate": 0.0,
    })
    with patch("app.api.questions.generate_question_for_criterion", return_value=mock_data):
        questions = client.post(f"/jobs/{job['id']}/questions/generate").json()

    qid = questions[0]["id"]
    response = client.patch(f"/questions/{qid}", json={"is_approved": True, "content": "Sửa lại"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_approved"] is True
    assert body["content"] == "Sửa lại"
    assert body["generated_by"] == "human_edited"

def test_generate_questions_partial_failure_keeps_successful_ones(client):
    """Đúng bug đã sửa: 1 criterion lỗi không được làm mất câu hỏi đã sinh thành
    công cho criterion khác trong cùng request."""
    _, job = _create_framework_and_job(client)

    good_result = ({"question": "Q tốt?", "rationale": "R"}, {
        "tokens_in": 5, "tokens_out": 5, "cost_estimate": 0.0,
    })
    with patch(
        "app.api.questions.generate_question_for_criterion",
        side_effect=[good_result, QuestionGenError("lỗi criterion thứ 2")],
    ):
        response = client.post(f"/jobs/{job['id']}/questions/generate")

    assert response.status_code == 200
    questions = response.json()
    assert len(questions) == 1
    assert questions[0]["content"] == "Q tốt?"