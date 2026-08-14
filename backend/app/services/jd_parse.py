import io

import pdfplumber
from docx import Document

# Ngưỡng đơn giản: JD thật luôn dài hơn nhiều so với ngưỡng này.
# Text ngắn hơn ngưỡng thường là dấu hiệu file scan ảnh hoặc bảng phức tạp
# không extract được đúng -> bắt buộc HR xem lại trước khi dùng.
MIN_TEXT_LENGTH_FOR_CONFIDENT_PARSE = 50


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, str]:
    """Trả về (text, status). status: 'parsed' hoặc 'needs_review'."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    text = "\n".join(text_parts).strip()
    status = "parsed" if len(text) >= MIN_TEXT_LENGTH_FOR_CONFIDENT_PARSE else "needs_review"
    return text, status


def extract_text_from_docx(file_bytes: bytes) -> tuple[str, str]:
    document = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    status = "parsed" if len(text) >= MIN_TEXT_LENGTH_FOR_CONFIDENT_PARSE else "needs_review"
    return text, status


def parse_jd_file(filename: str, file_bytes: bytes) -> tuple[str, str]:
    """Dispatch theo đuôi file. Ném ValueError nếu định dạng không hỗ trợ
    — API layer bắt lỗi này và trả 400, không để lỗi rơi xuống thành 500."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Định dạng file không hỗ trợ: {filename}. Chỉ nhận .pdf hoặc .docx")