import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.storage import upload_file
from app.models.session import Transcript
from app.models.user import User
from app.schemas.transcript import TranscriptResponse
from app.services.session_access import get_session_or_404, require_session_access
from app.services.stt import TranscriptionError, transcribe_audio

router = APIRouter(prefix="/sessions", tags=["transcripts"])

ALLOWED_AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".webm", ".ogg")
# STT chạy đồng bộ trong request (quyết định thiết kế Sprint 4) - giới hạn dung
# lượng để 1 file audio quá dài không chiếm dụng worker quá lâu, tránh nghẽn cả
# hệ thống chỉ vì 1 buổi phỏng vấn quên dừng ghi âm.
MAX_AUDIO_BYTES = 300 * 1024 * 1024  # ~300MB
RETENTION_DAYS = 180


@router.post("/{session_id}/transcript", response_model=TranscriptResponse, status_code=201)
async def upload_transcript_audio(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_session_or_404(session_id, db)
    # Kiểm tra quyền TRƯỚC khi đọc/validate file - không tốn công xử lý audio nếu
    # người gọi vốn không có quyền truy cập session này.
    require_session_access(session_id, user, db)

    if not file.filename or not file.filename.lower().endswith(ALLOWED_AUDIO_EXTENSIONS):
        raise HTTPException(400, f"Chỉ nhận file audio {ALLOWED_AUDIO_EXTENSIONS}")

    existing = db.query(Transcript).filter(Transcript.session_id == session_id).first()
    if existing is not None:
        raise HTTPException(
            409,
            "Session này đã có transcript - mỗi session chỉ ghi 1 audio dùng chung "
            "cho mọi interviewer, không upload đè.",
        )

    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            400,
            f"File audio quá lớn ({len(audio_bytes) / 1024 / 1024:.0f}MB) - "
            f"giới hạn {MAX_AUDIO_BYTES // 1024 // 1024}MB do STT chạy đồng bộ trong request.",
        )

    object_key = f"audio/{session_id}_{uuid.uuid4()}_{file.filename}"
    upload_file(object_key, audio_bytes, file.content_type or "application/octet-stream")

    transcript = Transcript(
        session_id=session_id,
        audio_file_path=object_key,
        status="processing",
        retention_expiry=datetime.now(UTC) + timedelta(days=RETENTION_DAYS),
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    # Transcribe SAU khi đã lưu record "processing" - nếu server crash giữa chừng,
    # ít nhất còn 1 record ở trạng thái processing để biết audio đã nhận, thay vì
    # mất dấu hoàn toàn.
    try:
        transcript.text = transcribe_audio(audio_bytes)
        transcript.status = "completed"
    except TranscriptionError:
        transcript.status = "failed"

    db.commit()
    db.refresh(transcript)
    return transcript


@router.get("/{session_id}/transcript", response_model=TranscriptResponse)
def get_transcript(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_session_or_404(session_id, db)
    require_session_access(session_id, user, db)

    transcript = db.query(Transcript).filter(Transcript.session_id == session_id).first()
    if transcript is None:
        raise HTTPException(404, "Session này chưa có transcript")
    return transcript