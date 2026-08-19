import json

from app.core.config import settings
from app.services.llm_client import LlmCallError, call_llm


class QuestionGenError(Exception):
    pass


def _build_prompt(criterion_name: str, scoring_rubric: str, jd_text: str) -> str:
    return f"""Bạn là chuyên gia thiết kế câu hỏi phỏng vấn kỹ thuật.

Tiêu chí cần đo: {criterion_name}
Rubric chấm điểm: {scoring_rubric}

Mô tả công việc (JD):
{jd_text}

Sinh ĐÚNG 1 câu hỏi phỏng vấn bằng tiếng Việt, bám sát ngữ cảnh cụ thể trong JD ở trên
(công nghệ, hệ thống, quy mô được nhắc tới), nhưng vẫn đo đúng tiêu chí đã cho.

Trả về CHÍNH XÁC định dạng JSON sau, không thêm text nào khác ngoài JSON:
{{"question": "...", "rationale": "giải thích ngắn vì sao câu hỏi này đo được tiêu chí"}}"""


def _mock_question_for_criterion(criterion_name: str, scoring_rubric: str) -> tuple[dict, dict]:
    """Trả về câu hỏi giả lập, không gọi API nào - dùng khi settings.llm_provider="mock"
    để dev/test luồng generate -> sensitive filter -> HITL mà không tốn credit/quota."""
    rubric_preview = scoring_rubric.strip()
    if len(rubric_preview) > 80:
        rubric_preview = rubric_preview[:80].rstrip() + "..."

    data = {
        "question": (
            f"[MOCK] Hãy kể một tình huống thực tế bạn từng xử lý thể hiện năng lực "
            f'"{criterion_name}", và cách bạn tự đánh giá kết quả của mình.'
        ),
        "rationale": (
            f'[MOCK] Câu hỏi giả lập để kiểm tra tiêu chí "{criterion_name}" '
            f"(rubric: {rubric_preview}) khi đang ở chế độ dev, không gọi LLM thật."
        ),
    }
    usage = {"tokens_in": 0, "tokens_out": 0, "cost_estimate": 0.0}
    return data, usage


def generate_question_for_criterion(
    criterion_name: str, scoring_rubric: str, jd_text: str
) -> tuple[dict, dict]:
    """Trả về (question_data, usage_data).
    question_data: {"question": str, "rationale": str}
    usage_data: {"tokens_in": int, "tokens_out": int, "cost_estimate": float}

    Provider được chọn qua settings.llm_provider: "mock" | "anthropic" | "groq".
    Ném QuestionGenError nếu response không parse được JSON đúng schema, hoặc nếu
    API của provider trả lỗi (hết credit, rate limit, auth, lỗi kết nối...)."""
    provider = settings.llm_provider

    if provider == "mock":
        return _mock_question_for_criterion(criterion_name, scoring_rubric)

    prompt = _build_prompt(criterion_name, scoring_rubric, jd_text)

    try:
        raw_text, usage = call_llm(prompt, max_tokens=500, json_mode=(provider == "groq"))
    except LlmCallError as e:
        raise QuestionGenError(f"Sinh câu hỏi thất bại: {e}") from e

    try:
        data = json.loads(raw_text)
        if "question" not in data or "rationale" not in data:
            raise ValueError("Thiếu field question/rationale")
    except (json.JSONDecodeError, ValueError) as e:
        raise QuestionGenError(f"{provider} trả về JSON không đúng schema: {raw_text}") from e

    return data, usage