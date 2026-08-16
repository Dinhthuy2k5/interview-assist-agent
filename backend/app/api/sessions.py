import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.db import get_db
from app.models.competency import Criterion
from app.models.job import Job
from app.models.question import Question
from app.models.session import InterviewerNote, InterviewSession, SessionInterviewer
from app.models.user import User, UserRole
from app.schemas.session import (
    NoteResponse,
    NoteUpsert,
    QuestionForSession,
    SessionCreate,
    SessionDetailResponse,
    SessionResponse,
    SessionStatusUpdate,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_session_or_404(session_id: uuid.UUID, db: Session) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session không tồn tại")
    return session


def _require_participant(session_id: uuid.UUID, user: User, db: Session) -> None:
    """Chặn interviewer xem/ghi note session mình không được gán - mỗi interviewer
    chỉ thao tác trên session của chính mình, kể cả khi biết session_id người khác."""
    is_participant = (
        db.query(SessionInterviewer)
        .filter(
            SessionInterviewer.session_id == session_id,
            SessionInterviewer.interviewer_id == user.id,
        )
        .first()
        is not None
    )
    if not is_participant:
        raise HTTPException(403, "Bạn không được gán vào session này")


@router.post(
    "",
    response_model=SessionResponse,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.hr_admin))],
)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    job = db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(404, "Job không tồn tại")

    invalid_ids = []
    for uid in payload.interviewer_ids:
        interviewer = db.get(User, uid)
        if interviewer is None or interviewer.role != UserRole.interviewer.value:
            invalid_ids.append(str(uid))
    if invalid_ids:
        raise HTTPException(
            400,
            f"interviewer_ids không hợp lệ (không tồn tại hoặc không phải role interviewer): {invalid_ids}",
        )

    session = InterviewSession(
        job_id=payload.job_id,
        candidate_name=payload.candidate_name,
        candidate_info=payload.candidate_info,
        scheduled_at=payload.scheduled_at,
    )
    db.add(session)
    db.flush()  # cần session.id trước khi tạo SessionInterviewer

    for interviewer_id in payload.interviewer_ids:
        db.add(SessionInterviewer(session_id=session.id, interviewer_id=interviewer_id))

    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    job_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    """HR Admin xem toàn bộ session (giám sát chung), lọc theo job nếu cần.
    Interviewer dùng /sessions/mine riêng - không thấy session của người khác."""
    query = db.query(InterviewSession)
    if job_id is not None:
        query = query.filter(InterviewSession.job_id == job_id)
    return query.order_by(InterviewSession.scheduled_at.desc()).all()


@router.get("/mine", response_model=list[SessionResponse])
def list_my_sessions(
    db: Session = Depends(get_db), user: User = Depends(require_role(UserRole.interviewer))
):
    return (
        db.query(InterviewSession)
        .join(SessionInterviewer, SessionInterviewer.session_id == InterviewSession.id)
        .filter(SessionInterviewer.interviewer_id == user.id)
        .order_by(InterviewSession.scheduled_at)
        .all()
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    session = _get_session_or_404(session_id, db)

    # hr_admin xem được mọi session (giám sát), interviewer chỉ xem được session
    # mình tham gia. Mọi role khác (council, hoặc role tương lai) CHƯA có use case
    # cho endpoint này - chặn tường minh thay vì để lọt qua vì không khớp interviewer.
    if user.role == UserRole.interviewer.value:
        _require_participant(session_id, user, db)
    elif user.role != UserRole.hr_admin.value:
        raise HTTPException(403, "Bạn không có quyền xem session này")

    # Join Criterion để lấy tên + rubric - thiếu 2 field này interviewer không biết
    # chấm điểm dựa trên tiêu chuẩn nào.
    rows = (
        db.query(Question, Criterion)
        .join(Criterion, Question.criterion_id == Criterion.id)
        .filter(Question.job_id == session.job_id, Question.is_approved.is_(True))
        .all()
    )
    questions = [
        QuestionForSession(
            id=q.id,
            criterion_id=q.criterion_id,
            criterion_name=c.name,
            scoring_rubric=c.scoring_rubric,
            content=q.content,
        )
        for q, c in rows
    ]

    my_notes = (
        db.query(InterviewerNote)
        .filter(InterviewerNote.session_id == session_id, InterviewerNote.interviewer_id == user.id)
        .all()
    )

    return SessionDetailResponse(
        session=SessionResponse.model_validate(session),
        questions=questions,
        my_notes=[NoteResponse.model_validate(n) for n in my_notes],
    )


@router.put("/{session_id}/notes/{criterion_id}", response_model=NoteResponse)
def upsert_note(
    session_id: uuid.UUID,
    criterion_id: uuid.UUID,
    payload: NoteUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.interviewer)),
):
    _get_session_or_404(session_id, db)
    _require_participant(session_id, user, db)

    note = (
        db.query(InterviewerNote)
        .filter(
            InterviewerNote.session_id == session_id,
            InterviewerNote.interviewer_id == user.id,
            InterviewerNote.criterion_id == criterion_id,
        )
        .first()
    )
    if note is None:
        note = InterviewerNote(
            session_id=session_id, interviewer_id=user.id, criterion_id=criterion_id
        )
        db.add(note)

    note.score = payload.score
    note.note_text = payload.note_text
    db.commit()
    db.refresh(note)
    return note


@router.patch("/{session_id}/status", response_model=SessionResponse)
def update_session_status(
    session_id: uuid.UUID,
    payload: SessionStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session_or_404(session_id, db)
    if user.role == UserRole.interviewer.value:
        _require_participant(session_id, user, db)
    elif user.role != UserRole.hr_admin.value:
        raise HTTPException(403, "Bạn không có quyền đổi trạng thái session này")

    session.status = payload.status
    db.commit()
    db.refresh(session)
    return session