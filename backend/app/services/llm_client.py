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


class LlmCallError(Exception):
    pass


def call_llm(prompt: str, max_tokens: int, json_mode: bool = False) -> tuple[str, dict]:
    """Gọi LLM THẬT theo settings.llm_provider ("anthropic" | "groq") - dùng chung
    cho mọi service cần gọi LLM (question_gen, aggregation, ...), tránh mỗi service
    tự viết lại toàn bộ logic chọn provider/tính cost/xử lý lỗi riêng - đây chính
    là lý do aggregation.py từng gọi thẳng Anthropic dù đã có Groq free tier từ
    Sprint 2: logic provider-switching không được tách dùng chung nên bị bỏ sót.

    KHÔNG xử lý "mock" ở đây - nội dung mock khác nhau tuỳ mục đích dùng (question_gen
    cần JSON question/rationale, aggregation cần đoạn tóm tắt tự do) nên mỗi service
    tự viết mock riêng, chỉ dùng chung phần gọi API thật.

    Trả về (raw_text, usage_data). Ném LlmCallError nếu API lỗi hoặc provider không hợp lệ."""
    provider = settings.llm_provider

    if provider == "anthropic":
        raw_text, tokens_in, tokens_out = _call_anthropic(prompt, max_tokens)
    elif provider == "groq":
        raw_text, tokens_in, tokens_out = _call_groq(prompt, max_tokens, json_mode)
    else:
        raise LlmCallError(
            f'settings.llm_provider không hợp lệ cho lời gọi LLM thật: {provider!r} '
            f'(chỉ nhận "anthropic", "groq" - "mock" phải được xử lý riêng ở service gọi)'
        )

    price_in = PRICE_PER_M_INPUT.get(provider, 0.0)
    price_out = PRICE_PER_M_OUTPUT.get(provider, 0.0)
    cost_estimate = (tokens_in / 1_000_000 * price_in) + (tokens_out / 1_000_000 * price_out)

    return raw_text, {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_estimate": round(cost_estimate, 6),
    }


def _call_anthropic(prompt: str, max_tokens: int) -> tuple[str, int, int]:
    """Trả về (raw_text, tokens_in, tokens_out). Ném LlmCallError nếu API lỗi."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        # Gồm BadRequestError (vd. hết credit), RateLimitError, AuthenticationError,
        # APIConnectionError, APITimeoutError... - đều là subclass của APIError.
        raise LlmCallError(f"Anthropic API lỗi: {e}") from e

    raw_text = "".join(block.text for block in response.content if block.type == "text")
    return raw_text, response.usage.input_tokens, response.usage.output_tokens


def _call_groq(prompt: str, max_tokens: int, json_mode: bool) -> tuple[str, int, int]:
    """Trả về (raw_text, tokens_in, tokens_out). Ném LlmCallError nếu API lỗi.
    Groq SDK tương thích kiểu OpenAI (chat.completions), khác Anthropic (messages)."""
    client = groq.Groq(api_key=settings.groq_api_key)
    kwargs: dict = {}
    if json_mode:
        # Bắt buộc prompt phải có chữ "JSON" để dùng được response_format này -
        # caller (vd. question_gen._build_prompt) tự đảm bảo điều đó.
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
    except groq.APIError as e:
        # Gồm RateLimitError (dễ gặp nhất do free tier giới hạn 30 req/phút),
        # AuthenticationError, APIConnectionError...
        raise LlmCallError(f"Groq API lỗi: {e}") from e

    raw_text = response.choices[0].message.content or ""
    usage = response.usage
    return raw_text, usage.prompt_tokens, usage.completion_tokens