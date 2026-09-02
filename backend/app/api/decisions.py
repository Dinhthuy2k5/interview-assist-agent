import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.models.decision import SessionDecision
from app.models.user import User, UserRole
from app.schemas.decision import DecisionCreate, DecisionResponse
from app.services.audit import log_action
from app.services.session_access import get_session_or_404

router = APIRouter(prefix="/sessions", tags=["decisions"])


def _to_response(decision: SessionDecision, db: Session) -> DecisionResponse:
    decider = db.get(User, decision.decided_by)
    return DecisionResponse(
        id=decision.id,
        session_id=decision.session_id,
        decided_by=decision.decided_by,
        decided_by_name=decider.full_name if decider else "(người dùng không xác định)",
        decision=decision.decision,
        rationale=decision.rationale,
        created_at=decision.created_at,
    )


@router.post(
    "/{session_id}/decision",
    response_model=DecisionResponse,
    status_code=201,
)
def create_decision(
    session_id: uuid.UUID,
    payload: DecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.council)),
):
    """Chỉ Council được ghi quyết định (đúng vai trò 'ra quyết định cuối'). Không
    check tồn tại AggregationReport trước - Council có quyền quyết định dựa trên
    thông tin họ có, hệ thống không được áp đặt phải có report mới cho quyết định."""
    get_session_or_404(session_id, db)

    decision = SessionDecision(
        session_id=session_id,
        decided_by=current_user.id,
        decision=payload.decision,
        rationale=payload.rationale,
    )
    db.add(decision)
    db.flush()  # cần decision.id trước khi ghi log

    log_action(
        db,
        actor_id=current_user.id,
        action="decision_created",
        target_type="session",
        target_id=str(session_id),
        detail=f"decision={payload.decision}",
    )
    db.commit()
    db.refresh(decision)
    return _to_response(decision, db)


@router.get(
    "/{session_id}/decisions",
    response_model=list[DecisionResponse],
    dependencies=[Depends(require_role(UserRole.hr_admin, UserRole.council))],
)
def list_decisions(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """Toàn bộ lịch sử quyết định (append-only) - dòng đầu tiên trong response
    (created_at mới nhất) là quyết định HIỆN TẠI. HR Admin xem để biết kết quả
    cuối cùng, không được tự ghi quyết định."""
    get_session_or_404(session_id, db)
    decisions = (
        db.query(SessionDecision)
        .filter(SessionDecision.session_id == session_id)
        .order_by(SessionDecision.created_at.desc())
        .all()
    )
    return [_to_response(d, db) for d in decisions]