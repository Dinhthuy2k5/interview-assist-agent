import json

import anthropic

from app.core.config import settings

MODEL = "claude-sonnet-4-5"

# Đơn giá tham khảo (USD / 1M token) - cần cập nhật nếu Anthropic đổi giá.
# Đặt hằng số ở đây thay vì hardcode trong hàm để dễ sửa 1 chỗ.
PRICE_PER_M_INPUT = 3.0
PRICE_PER_M_OUTPUT = 15.0


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


def generate_question_for_criterion(
    criterion_name: str, scoring_rubric: str, jd_text: str
) -> tuple[dict, dict]:
    """Trả về (question_data, usage_data).
    question_data: {"question": str, "rationale": str}
    usage_data: {"tokens_in": int, "tokens_out": int, "cost_estimate": float}
    Ném QuestionGenError nếu response không parse được JSON đúng schema."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = _build_prompt(criterion_name, scoring_rubric, jd_text)

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = "".join(block.text for block in response.content if block.type == "text")
    try:
        data = json.loads(raw_text)
        if "question" not in data or "rationale" not in data:
            raise ValueError("Thiếu field question/rationale")
    except (json.JSONDecodeError, ValueError) as e:
        raise QuestionGenError(f"Claude trả về JSON không đúng schema: {raw_text}") from e

    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    cost_estimate = (tokens_in / 1_000_000 * PRICE_PER_M_INPUT) + (
        tokens_out / 1_000_000 * PRICE_PER_M_OUTPUT
    )

    return data, {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_estimate": round(cost_estimate, 6),
    }