import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.models.competency import CompetencyFramework
from app.models.job import Job
from app.models.llm_usage_log import LlmUsageLog
from app.models.question import Question
from app.models.user import User, UserRole
from app.schemas.question import QuestionResponse, QuestionUpdate
from app.services.question_gen import QuestionGenError, generate_question_for_criterion
from app.services.sensitive_filter import check_sensitive_content

router = APIRouter(tags=["questions"])


@router.post("/jobs/{job_id}/questions/generate", response_model=list[QuestionResponse])
def generate_questions(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job không tồn tại")
    if not job.jd_text:
        raise HTTPException(400, "Job chưa có jd_text - parse hoặc sửa JD trước khi sinh câu hỏi")

    framework = db.get(CompetencyFramework, job.framework_id)
    if not framework or not framework.criteria:
        raise HTTPException(400, "Framework của job này chưa có criterion nào")

    created_questions = []
    failed_criteria = []
    for criterion in framework.criteria:
        try:
            data, usage = generate_question_for_criterion(
                criterion.name, criterion.scoring_rubric, job.jd_text
            )
        except QuestionGenError:
            # Không để 1 criterion lỗi làm mất câu hỏi đã sinh thành công cho các
            # criterion khác - ghi nhận lỗi, tiếp tục xử lý phần còn lại, commit
            # từng câu ngay để không phụ thuộc vào toàn bộ vòng lặp chạy trót lọt.
            failed_criteria.append(criterion.name)
            continue

        db.add(
            LlmUsageLog(
                service="question_gen",
                tokens_in=usage["tokens_in"],
                tokens_out=usage["tokens_out"],
                cost_estimate=usage["cost_estimate"],
            )
        )

        is_flagged, flag_reason = check_sensitive_content(data["question"])

        question = Question(
            job_id=job.id,
            criterion_id=criterion.id,
            content=data["question"],
            rationale=data["rationale"],
            generated_by="agent",
            is_sensitive_flagged=is_flagged,
            sensitive_flag_reason=flag_reason,
            is_approved=False,
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        created_questions.append(question)

    if failed_criteria and not created_questions:
        raise HTTPException(
            502, f"Sinh câu hỏi thất bại cho tất cả tiêu chí: {', '.join(failed_criteria)}"
        )

    # Không trả về câu hỏi đã bị sensitive filter chặn - giữ nhất quán với
    # list_questions (HR không cần thấy câu bị flag). Câu bị flag vẫn được
    # lưu trong DB để audit sau này, chỉ không xuất hiện trong response.
    return [q for q in created_questions if not q.is_sensitive_flagged]


@router.get("/jobs/{job_id}/questions", response_model=list[QuestionResponse])
def list_questions(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    # TODO: khi Interviewer có UI xem câu hỏi đã duyệt trước buổi phỏng vấn
    # (Sprint sau), nới quyền này thành require_role(hr_admin, interviewer).
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    """Chỉ trả câu hỏi CHƯA bị sensitive filter chặn - HR không cần thấy câu bị flag,
    chỉ cần biết nó đã bị lọc (xem qua endpoint riêng nếu cần audit sau này)."""
    return (
        db.query(Question)
        .filter(Question.job_id == job_id, Question.is_sensitive_flagged.is_(False))
        .all()
    )


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(404, "Question không tồn tại")

    if payload.content is not None:
        question.content = payload.content
        question.generated_by = "human_edited"
        # Nội dung đã đổi -> re-check sensitive filter, không giữ nguyên
        # flag cũ (có thể đã lỗi thời hoặc không còn đúng với nội dung mới).
        is_flagged, flag_reason = check_sensitive_content(question.content)
        question.is_sensitive_flagged = is_flagged
        question.sensitive_flag_reason = flag_reason

    if payload.is_approved is not None:
        if payload.is_approved and question.is_sensitive_flagged:
            raise HTTPException(
                400,
                "Không thể duyệt câu hỏi đang bị đánh dấu nhạy cảm - "
                "sửa nội dung để bỏ flag trước khi duyệt",
            )
        question.is_approved = payload.is_approved

    db.commit()
    db.refresh(question)
    return question