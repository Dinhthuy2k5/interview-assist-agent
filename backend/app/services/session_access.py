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
    """hr_admin luôn được phép; interviewer chỉ khi là participant; mọi role khác
    (council, hoặc role tương lai) bị chặn TƯỜNG MINH.

    Dùng cho các hành động THAO TÁC trên session - đổi status, upload/đọc
    transcript. Council KHÔNG có trong hàm này dù đã được cấp quyền xem chi tiết
    (xem require_session_read_access) - xem chi tiết (câu hỏi đã hỏi) khác hẳn về
    bản chất với sửa trạng thái hay truy cập bản ghi âm gốc, không nên gộp chung
    1 hàm rồi vô tình cấp thừa quyền khi mở rộng quyền xem."""
    if user.role == UserRole.hr_admin.value:
        return
    if user.role == UserRole.interviewer.value:
        require_participant(session_id, user, db)
        return
    raise HTTPException(403, "Bạn không có quyền truy cập session này")


def require_session_read_access(session_id: uuid.UUID, user: User, db: Session) -> None:
    """Phiên bản MỞ HƠN require_session_access - CHỈ dùng cho endpoint xem chi
    tiết session (GET .../sessions/{id}, hiện câu hỏi đã duyệt). Council cần xem
    được để "ra quyết định cuối" (đúng nhu cầu từ Phân tích ban đầu), nhưng KHÔNG
    được cấp thêm quyền đổi status hay đụng transcript qua hàm này - những hành
    động đó vẫn dùng require_session_access, Council không nằm trong đó."""
    if user.role in (UserRole.hr_admin.value, UserRole.council.value):
        return
    if user.role == UserRole.interviewer.value:
        require_participant(session_id, user, db)
        return
    raise HTTPException(403, "Bạn không có quyền truy cập session này")