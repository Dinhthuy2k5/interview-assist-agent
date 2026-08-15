import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_role
from app.core.db import get_db
from app.models.competency import CompetencyFramework, Criterion
from app.models.user import User, UserRole
from app.schemas.competency import (
    CompetencyFrameworkCreate,
    CompetencyFrameworkResponse,
    CompetencyFrameworkUpdate,
)

router = APIRouter(prefix="/frameworks", tags=["competency-frameworks"])


def _get_framework_or_404(framework_id: uuid.UUID, db: Session) -> CompetencyFramework:
    framework = (
        db.query(CompetencyFramework)
        .options(selectinload(CompetencyFramework.criteria))
        .filter(CompetencyFramework.id == framework_id)
        .first()
    )
    if not framework:
        raise HTTPException(404, "Framework không tồn tại")
    return framework


@router.post("", response_model=CompetencyFrameworkResponse, status_code=201)
def create_framework(
    payload: CompetencyFrameworkCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    framework = CompetencyFramework(name=payload.name, description=payload.description)
    framework.criteria = [
        Criterion(name=c.name, weight=c.weight, scoring_rubric=c.scoring_rubric)
        for c in payload.criteria
    ]
    db.add(framework)
    db.commit()
    db.refresh(framework)
    return framework


@router.get("", response_model=list[CompetencyFrameworkResponse])
def list_frameworks(
    db: Session = Depends(get_db),
    # TODO: khi Interviewer/Council cần xem framework (Sprint sau), nới quyền này.
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    return (
        db.query(CompetencyFramework).options(selectinload(CompetencyFramework.criteria)).all()
    )


@router.get("/{framework_id}", response_model=CompetencyFrameworkResponse)
def get_framework(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    return _get_framework_or_404(framework_id, db)


@router.patch("/{framework_id}", response_model=CompetencyFrameworkResponse)
def update_framework(
    framework_id: uuid.UUID,
    payload: CompetencyFrameworkUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    framework = _get_framework_or_404(framework_id, db)
    if payload.name is not None:
        framework.name = payload.name
    if payload.description is not None:
        framework.description = payload.description
    db.commit()
    db.refresh(framework)
    return framework


@router.delete("/{framework_id}", status_code=204)
def delete_framework(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    framework = _get_framework_or_404(framework_id, db)
    # Criterion có ondelete="CASCADE" -> xoá framework tự xoá theo criteria.
    # Job.framework_id KHÔNG có CASCADE (cố ý) -> nếu có Job đang dùng framework
    # này, DB sẽ chặn xoá bằng IntegrityError. Bắt lỗi đó trả về 409 cho rõ nghĩa
    # thay vì để lộ ra 500.
    try:
        db.delete(framework)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            409, "Không thể xoá framework đang được Job sử dụng"
        ) from e