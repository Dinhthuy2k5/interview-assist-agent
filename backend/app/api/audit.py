from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get(
    "",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(require_role(UserRole.hr_admin))],
)
def list_audit_log(limit: int = 100, db: Session = Depends(get_db)):
    """Chỉ HR Admin xem - đây là dữ liệu bảo mật (ai đăng nhập, ai tạo/sửa tài
    khoản, ai ra quyết định). limit mặc định 100, tránh trả về toàn bộ log nếu
    bảng lớn dần theo thời gian - chưa có phân trang đầy đủ, đủ dùng cho quy mô
    hiện tại."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()

    result = []
    for log in logs:
        actor = db.get(User, log.actor_id) if log.actor_id else None
        result.append(
            AuditLogResponse(
                id=log.id,
                actor_id=log.actor_id,
                actor_name=actor.full_name if actor else None,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                detail=log.detail,
                created_at=log.created_at,
            )
        )
    return result   