import uuid

from app.core.config import settings
from app.models.llm_usage_log import LlmUsageLog
from app.services.embedding import compute_similarity
from app.services.llm_client import LlmCallError, call_llm

RULE_BASED_VARIANCE_THRESHOLD = 2  # chênh lệch điểm tối đa cho phép (thang 1-5)
EMBEDDING_SIMILARITY_THRESHOLD = 0.6  # dưới ngưỡng này coi là "lý do khác biệt đáng kể"


class SemanticCheckError(Exception):
    pass


def build_interviewer_labels(interviewer_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    """Gán label ẩn danh ổn định ("Người phỏng vấn N") theo 1 thứ tự CỐ ĐỊNH duy
    nhất cho toàn bộ interviewer trong session - PHẢI dùng đúng 1 map này cho MỌI
    criterion trong cùng 1 lần tổng hợp, không được tính lại theo từng criterion.

    Đây là fix cho bug đã phát hiện: trước đây label gán theo enumerate(notes) của
    TỪNG criterion riêng lẻ - nếu 1 interviewer bỏ sót note ở 1 criterion, "Người
    phỏng vấn 1" ở 2 criterion có thể là 2 người khác nhau, phá hỏng mục đích ẩn
    danh nhất quán. Tách thành hàm thuần (không đụng DB) để test được ổn định,
    không phụ thuộc thứ tự DB trả về (không đảm bảo nếu nhiều dòng cùng insert
    trong 1 transaction - vd. Postgres func.now() trả cùng 1 giá trị cho cả
    transaction, không phân biệt được thứ tự insert thật)."""
    return {interviewer_id: f"Người phỏng vấn {i + 1}" for i, interviewer_id in enumerate(interviewer_ids)}

def get_ordered_participants(session_id: uuid.UUID, db) -> list:
    """order_by created_at + id (tie-break): Postgres func.now() trả CÙNG 1 giá
    trị cho mọi statement trong 1 transaction - nhiều SessionInterviewer tạo cùng
    lúc (đúng trường hợp thực tế khi POST /sessions) chỉ order theo created_at
    không đảm bảo thứ tự ổn định giữa các lần query khác nhau. Tách hàm này để
    aggregate_session() và endpoint GET .../notes DÙNG CHUNG - nếu 2 nơi tự viết
    order_by riêng, dễ lệch nhau và "Người phỏng vấn 1" ở report với ở note gốc
    lại là 2 người khác nhau."""
    from app.models.session import SessionInterviewer

    return (
        db.query(SessionInterviewer)
        .filter(SessionInterviewer.session_id == session_id)
        .order_by(SessionInterviewer.created_at, SessionInterviewer.id)
        .all()
    )


def detect_conflict(scores: list[int], note_texts: list[str]) -> tuple[bool, str | None]:
    """Trả về (has_conflict, conflict_type). conflict_type: 'rule_based' | 'embedding' | None.

    Rule-based chạy trước (rẻ, tức thời). Chỉ khi rule-based KHÔNG flag mới chạy
    embedding check - đúng thiết kế gốc: embedding bắt trường hợp BÙ (điểm giống
    nhau nhưng note khác biệt), không phải chạy song song lãng phí."""
    if len(scores) >= 2 and (max(scores) - min(scores)) >= RULE_BASED_VARIANCE_THRESHOLD:
        return True, "rule_based"

    non_empty_texts = [t for t in note_texts if t and t.strip()]
    if len(non_empty_texts) >= 2:
        similarities = []
        for i in range(len(non_empty_texts)):
            for j in range(i + 1, len(non_empty_texts)):
                similarities.append(compute_similarity(non_empty_texts[i], non_empty_texts[j]))
        if similarities and min(similarities) < EMBEDDING_SIMILARITY_THRESHOLD:
            return True, "embedding"

    return False, None


def compute_weighted_average(criterion_averages: list[tuple[float, float]]) -> float | None:
    """criterion_averages: list[(average_score, criterion_weight)] - chỉ tính trên
    criteria có ít nhất 1 note, trả None nếu không có criteria nào có dữ liệu."""
    total_weight = sum(w for _, w in criterion_averages)
    if total_weight == 0:
        return None
    return sum(avg * w for avg, w in criterion_averages) / total_weight


def compute_overall_recommendation(weighted_average: float | None) -> str:
    if weighted_average is None:
        return "Chưa đủ dữ liệu"
    if weighted_average >= 4.0:
        return "Đề xuất tuyển"
    if weighted_average >= 2.5:
        return "Cần thảo luận thêm"
    return "Không đề xuất"


def _mock_conflict_summary(criterion_name: str, notes: list[dict]) -> str:
    """Dùng khi settings.llm_provider="mock" - dev/test luồng aggregate không tốn
    credit/quota, giống pattern _mock_question_for_criterion ở question_gen.py."""
    return (
        f'[MOCK] Các interviewer có đánh giá khác biệt ở tiêu chí "{criterion_name}" '
        f"({len(notes)} người tham gia) - xem note gốc của từng người để hiểu rõ "
        f"lý do khác biệt. Đây là tóm tắt giả lập, không gọi LLM thật."
    )


def summarize_conflict(criterion_name: str, notes: list[dict]) -> tuple[str, dict]:
    """notes: list[{"label": "Người phỏng vấn 1", "score": int|None, "note_text": str}]
    - label PHẢI được caller gán ổn định theo 1 thứ tự cố định của toàn bộ interviewer
    trong session (không phải theo thứ tự notes tồn tại cho riêng criterion này) -
    nếu không, "Người phỏng vấn 1" ở criterion A và "Người phỏng vấn 1" ở criterion B
    có thể là 2 người khác nhau, phá hỏng mục đích ẩn danh nhất quán.

    Trả về (summary_text, usage_data). Chỉ gọi khi đã bị flag conflict - kiểm soát
    chi phí, không chạy LLM cho mọi criterion. Dùng chung app.services.llm_client -
    tự động theo settings.llm_provider (mock/anthropic/groq), KHÔNG hard-code
    Anthropic - trước đây bug này khiến aggregate luôn tốn credit Anthropic dù đã
    có Groq free tier từ Sprint 2."""
    provider = settings.llm_provider

    if provider == "mock":
        return _mock_conflict_summary(criterion_name, notes), {
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_estimate": 0.0,
        }

    notes_text = "\n".join(
        f"- {n['label']}: điểm {n['score'] if n['score'] is not None else 'chưa chấm'}, "
        f"note: \"{n['note_text'] or '(không có ghi chú)'}\""
        for n in notes
    )
    prompt = f"""Các interviewer đánh giá tiêu chí "{criterion_name}" cho cùng 1 ứng viên như sau:

{notes_text}

Đây là những đánh giá có sự khác biệt đáng kể (về điểm số hoặc lý do). Viết 1 đoạn
tóm tắt ngắn (3-4 câu) bằng tiếng Việt nêu rõ điểm khác biệt là gì, KHÔNG tự đưa ra
kết luận ai đúng ai sai - hội đồng tuyển dụng sẽ tự xem note gốc và quyết định."""

    try:
        text, usage = call_llm(prompt, max_tokens=300)
    except LlmCallError as e:
        raise SemanticCheckError(f"Lỗi gọi LLM để giải thích conflict: {e}") from e

    return text.strip(), usage


def log_llm_usage(db, usage: dict) -> None:
    db.add(
        LlmUsageLog(
            service="aggregation_semantic_check",
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
            cost_estimate=usage["cost_estimate"],
        )
    )