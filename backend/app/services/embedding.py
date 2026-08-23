MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # hỗ trợ tiếng Việt
_model = None


def _get_model():
    """Lazy import + lazy load - giống pattern app/services/stt.py: import module
    này không bắt buộc cài sentence-transformers/tải model, test mock hoàn toàn
    không cần chạm tới model thật."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def compute_similarity(text_a: str, text_b: str) -> float:
    """Trả về cosine similarity [0, 1] giữa 2 đoạn text. Dùng để phát hiện trường
    hợp 2 interviewer cho điểm giống nhau nhưng lý do (note_text) khác biệt lớn -
    rule-based variance không bắt được case này vì chỉ nhìn vào điểm số."""
    from sentence_transformers import util

    model = _get_model()
    embeddings = model.encode([text_a, text_b])
    return float(util.cos_sim(embeddings[0], embeddings[1])[0][0])