import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.session import InterviewSession, SessionInterviewer
from app.models.user import User, UserRole


def get_session_or_404(session_id: uuid.UUID, db: Session) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Session không tồn tại")
    return session


def require_participant(session_id: uuid.UUID, user: User, db: Session) -> None:
    """Chặn interviewer thao tác trên session mình không được gán - mỗi interviewer
    chỉ động vào session của chính mình, kể cả khi biết session_id người khác."""
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


def require_session_access(session_id: uuid.UUID, user: User, db: Session) -> None:
    """hr_admin luôn được phép (giám sát); interviewer chỉ khi là participant; mọi
    role khác (council, hoặc role tương lai) bị chặn TƯỜNG MINH.

    Dùng chung cho mọi endpoint chỉ cần biết "có được truy cập session này không" -
    xem chi tiết, đổi status, upload/đọc transcript. Trước đây logic này viết lặp
    lại (if/elif) ở từng endpoint riêng, và đã từng sai 1 lần (thiếu elif khiến
    council lọt qua get_session_detail không kiểm tra gì) - gom về 1 chỗ để lỗi
    tương tự không thể tái diễn ở endpoint mới mà chỉ cần sửa 1 nơi."""
    if user.role == UserRole.hr_admin.value:
        return
    if user.role == UserRole.interviewer.value:
        require_participant(session_id, user, db)
        return
    raise HTTPException(403, "Bạn không có quyền truy cập session này")