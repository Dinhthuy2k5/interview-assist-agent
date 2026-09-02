import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_action(
    db: Session,
    actor_id: uuid.UUID | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: str | None = None,
) -> None:
    """Ghi 1 dòng audit log - KHÔNG tự commit, để caller gộp chung transaction với
    hành động chính (rollback đồng bộ nếu hành động chính lỗi giữa chừng, tránh
    tình trạng log được ghi nhưng hành động thật lại không xảy ra)."""
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
    )