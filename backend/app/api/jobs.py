import uuid
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.core.storage import upload_file
from app.models.job import Job
from app.models.user import User, UserRole
from app.schemas.job import JobResponse, JobUpdate
from app.services.jd_parse import parse_jd_file

router = APIRouter(prefix="/jobs", tags=["jobs"])

ALLOWED_EXTENSIONS = (".pdf", ".docx")


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    title: str = Form(...),
    level: str = Form(...),
    framework_id: uuid.UUID = Form(...),
    application_deadline: date | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.hr_admin)),
):
    if not file.filename or not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(400, f"Chỉ nhận file {ALLOWED_EXTENSIONS}")

    file_bytes = await file.read()
    try:
        jd_text, jd_parse_status = parse_jd_file(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    object_key = f"jd/{uuid.uuid4()}_{file.filename}"
    upload_file(object_key, file_bytes, file.content_type or "application/octet-stream")

    job = Job(
        title=title,
        level=level,
        jd_file_path=object_key,
        jd_text=jd_text,
        jd_parse_status=jd_parse_status,
        framework_id=framework_id,
        created_by=current_user.full_name,
        application_deadline=application_deadline,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobResponse])
def list_jobs(
    status: Literal["all", "open", "closed"] = "all",
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    """Lọc theo status tính động (không phải cột DB) - ổn ở quy mô hiện tại, nếu
    số lượng job lớn lên nhiều nên đẩy điều kiện lọc xuống SQL thay vì lọc bằng
    Python sau khi đã fetch hết."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    if status == "all":
        return jobs

    today = datetime.now(UTC).date()

    def is_open(j: Job) -> bool:
        if j.is_closed:
            return False
        return j.application_deadline is None or j.application_deadline >= today

    if status == "open":
        return [j for j in jobs if is_open(j)]
    return [j for j in jobs if not is_open(j)]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job không tồn tại")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: uuid.UUID,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    """HR sửa jd_text sau khi xem needs_review. Sửa xong tự chuyển status -> parsed
    (giả định HR đã xác nhận nội dung đúng khi họ chủ động sửa). Cũng dùng chung
    endpoint này để set/sửa hạn nộp hồ sơ hoặc đóng tuyển tay."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job không tồn tại")
    if payload.jd_text is not None:
        job.jd_text = payload.jd_text
        job.jd_parse_status = "parsed"
    if payload.application_deadline is not None:
        job.application_deadline = payload.application_deadline
    if payload.is_closed is not None:
        job.is_closed = payload.is_closed
    db.commit()
    db.refresh(job)
    return job