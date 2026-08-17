import io

MODEL_SIZE = "base"
_model = None


class TranscriptionError(Exception):
    pass


def _get_model():
    """Lazy import + lazy load model - tránh việc chỉ import module này (qua chuỗi
    import từ api/sessions.py) đã bắt buộc cài faster-whisper + tải model, kể cả
    khi test chỉ mock transcribe_audio và không bao giờ chạm tới model thật."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_bytes: bytes) -> str:
    """Chạy đồng bộ (blocking) trong request - chấp nhận được cho MVP vì đây là
    tính năng batch (xử lý sau buổi phỏng vấn, không real-time), nhưng audio dài
    có thể khiến request timeout ở proxy/browser mặc định. Backlog: chuyển sang
    background task queue khi có nhiều session xử lý cùng lúc."""
    try:
        model = _get_model()
        segments, _ = model.transcribe(io.BytesIO(audio_bytes), language="vi")
        return " ".join(seg.text.strip() for seg in segments).strip()
    except Exception as e:
        raise TranscriptionError(f"Lỗi khi transcribe audio: {e}") from e