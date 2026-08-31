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
from app.services.session_access import (
    get_session_or_404,
    require_participant,
    require_session_access,
    require_session_read_access,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


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
    _: User = Depends(require_role(UserRole.hr_admin, UserRole.council)),
):
    """HR Admin xem toàn bộ session (giám sát chung) hoặc lọc theo job. Council
    cũng cần endpoint này để biết session nào tồn tại trước khi đọc report tổng
    hợp / chi tiết session. Interviewer dùng /sessions/mine riêng."""
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
    session = get_session_or_404(session_id, db)
    # Dùng bản MỞ HƠN (require_session_read_access) - Council cần xem câu hỏi đã
    # hỏi để ra quyết định cuối, khác với require_session_access (đổi status,
    # transcript) vốn không cấp cho Council.
    require_session_read_access(session_id, user, db)

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

    # my_notes lọc theo user.id - hr_admin/council không phải interviewer nên
    # luôn rỗng ở đây (đúng, không phải bug) - họ xem note gốc qua endpoint riêng
    # GET .../notes (app/api/aggregation.py) sau khi đã có report tổng hợp.
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
    get_session_or_404(session_id, db)
    require_participant(session_id, user, db)

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
    session = get_session_or_404(session_id, db)
    # Vẫn dùng require_session_access (KHÔNG phải bản _read_access) - Council xem
    # được chi tiết nhưng không được đổi trạng thái vận hành của session.
    require_session_access(session_id, user, db)

    session.status = payload.status
    db.commit()
    db.refresh(session)
    return session