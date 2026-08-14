import json

import anthropic
import groq

from app.core.config import settings

ANTHROPIC_MODEL = "claude-sonnet-4-5"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Đơn giá tham khảo (USD / 1M token) - chỉ để ước tính cost_estimate ghi log, KHÔNG
# phản ánh việc bị tính phí thật (Groq free tier hiện không tính phí theo token, chỉ
# giới hạn theo rate limit). Cập nhật nếu nhà cung cấp đổi giá hoặc bạn đổi model.
PRICE_PER_M_INPUT = {
    "anthropic": 3.0,
    "groq": 0.59,
}
PRICE_PER_M_OUTPUT = {
    "anthropic": 15.0,
    "groq": 0.79,
}


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


def _call_anthropic(prompt: str) -> tuple[str, int, int]:
    """Trả về (raw_text, tokens_in, tokens_out). Ném QuestionGenError nếu API lỗi."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        # Gồm BadRequestError (vd. hết credit), RateLimitError, AuthenticationError,
        # APIConnectionError, APITimeoutError... - đều là subclass của APIError.
        raise QuestionGenError(f"Anthropic API lỗi khi sinh câu hỏi: {e}") from e

    raw_text = "".join(block.text for block in response.content if block.type == "text")
    return raw_text, response.usage.input_tokens, response.usage.output_tokens


def _call_groq(prompt: str) -> tuple[str, int, int]:
    """Trả về (raw_text, tokens_in, tokens_out). Ném QuestionGenError nếu API lỗi.
    Groq SDK tương thích kiểu OpenAI (chat.completions), khác Anthropic (messages)."""
    client = groq.Groq(api_key=settings.groq_api_key)
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=500,
            # Bắt buộc phải có chữ "JSON" trong prompt để dùng được response_format
            # này - prompt hiện tại đã có, response_format giúp giảm rủi ro model trả
            # text kèm giải thích thay vì JSON thuần.
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
    except groq.APIError as e:
        # Gồm RateLimitError (dễ gặp nhất do free tier giới hạn 30 req/phút),
        # AuthenticationError, APIConnectionError...
        raise QuestionGenError(f"Groq API lỗi khi sinh câu hỏi: {e}") from e

    raw_text = response.choices[0].message.content or ""
    usage = response.usage
    return raw_text, usage.prompt_tokens, usage.completion_tokens


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

    if provider == "anthropic":
        raw_text, tokens_in, tokens_out = _call_anthropic(prompt)
    elif provider == "groq":
        raw_text, tokens_in, tokens_out = _call_groq(prompt)
    else:
        raise QuestionGenError(
            f'settings.llm_provider không hợp lệ: {provider!r} (chỉ nhận "mock", "anthropic", "groq")'
        )

    try:
        data = json.loads(raw_text)
        if "question" not in data or "rationale" not in data:
            raise ValueError("Thiếu field question/rationale")
    except (json.JSONDecodeError, ValueError) as e:
        raise QuestionGenError(f"{provider} trả về JSON không đúng schema: {raw_text}") from e

    price_in = PRICE_PER_M_INPUT.get(provider, 0.0)
    price_out = PRICE_PER_M_OUTPUT.get(provider, 0.0)
    cost_estimate = (tokens_in / 1_000_000 * price_in) + (tokens_out / 1_000_000 * price_out)

    return data, {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_estimate": round(cost_estimate, 6),
    }