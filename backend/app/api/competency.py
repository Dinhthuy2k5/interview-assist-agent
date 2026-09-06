import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.cache import delete_cached, get_cached, set_cached
from app.core.db import get_db
from app.models.competency import CompetencyFramework, Criterion
from app.schemas.competency import (
    CompetencyFrameworkCreate,
    CompetencyFrameworkResponse,
    CompetencyFrameworkUpdate,
)

router = APIRouter(prefix="/frameworks", tags=["competency-frameworks"])

FRAMEWORKS_LIST_CACHE_KEY = "frameworks:all"
CACHE_TTL_SECONDS = 300  # 5 phút - lưới an toàn cuối nếu quên invalidate ở đâu đó


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
def create_framework(payload: CompetencyFrameworkCreate, db: Session = Depends(get_db)):
    framework = CompetencyFramework(name=payload.name, description=payload.description)
    framework.criteria = [
        Criterion(name=c.name, weight=c.weight, scoring_rubric=c.scoring_rubric)
        for c in payload.criteria
    ]
    db.add(framework)
    db.commit()
    db.refresh(framework)

    delete_cached(FRAMEWORKS_LIST_CACHE_KEY)
    return framework


@router.get("", response_model=list[CompetencyFrameworkResponse])
def list_frameworks(db: Session = Depends(get_db)):
    cached = get_cached(FRAMEWORKS_LIST_CACHE_KEY)
    if cached is not None:
        return cached

    frameworks = (
        db.query(CompetencyFramework).options(selectinload(CompetencyFramework.criteria)).all()
    )
    result = [CompetencyFrameworkResponse.model_validate(f).model_dump(mode="json") for f in frameworks]
    set_cached(FRAMEWORKS_LIST_CACHE_KEY, result, ttl_seconds=CACHE_TTL_SECONDS)
    return result


@router.get("/{framework_id}", response_model=CompetencyFrameworkResponse)
def get_framework(framework_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_framework_or_404(framework_id, db)


@router.patch("/{framework_id}", response_model=CompetencyFrameworkResponse)
def update_framework(
    framework_id: uuid.UUID, payload: CompetencyFrameworkUpdate, db: Session = Depends(get_db)
):
    framework = _get_framework_or_404(framework_id, db)
    if payload.name is not None:
        framework.name = payload.name
    if payload.description is not None:
        framework.description = payload.description
    db.commit()
    db.refresh(framework)

    delete_cached(FRAMEWORKS_LIST_CACHE_KEY)
    return framework


@router.delete("/{framework_id}", status_code=204)
def delete_framework(framework_id: uuid.UUID, db: Session = Depends(get_db)):
    framework = _get_framework_or_404(framework_id, db)
    try:
        db.delete(framework)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(409, "Không thể xoá framework đang được Job sử dụng") from e

    delete_cached(FRAMEWORKS_LIST_CACHE_KEY)