import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.storage import upload_file
from app.models.job import Job
from app.schemas.job import JobResponse, JobUpdate
from app.services.jd_parse import parse_jd_file

router = APIRouter(prefix="/jobs", tags=["jobs"])

ALLOWED_EXTENSIONS = (".pdf", ".docx")


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    title: str = Form(...),
    level: str = Form(...),
    framework_id: uuid.UUID = Form(...),
    created_by: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
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
        created_by=created_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job không tồn tại")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(job_id: uuid.UUID, payload: JobUpdate, db: Session = Depends(get_db)):
    """HR sửa jd_text sau khi xem needs_review. Sửa xong tự chuyển status -> parsed
    (giả định HR đã xác nhận nội dung đúng khi họ chủ động sửa)."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job không tồn tại")
    if payload.jd_text is not None:
        job.jd_text = payload.jd_text
        job.jd_parse_status = "parsed"
    db.commit()
    db.refresh(job)
    return job