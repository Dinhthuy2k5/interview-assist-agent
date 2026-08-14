import io

from docx import Document
from reportlab.pdfgen import canvas

from app.services.jd_parse import (
    extract_text_from_docx,
    extract_text_from_pdf,
    parse_jd_file,
)

SAMPLE_JD_TEXT = (
    "Senior Backend Engineer. Yeu cau: 5 nam kinh nghiem Python, "
    "hieu biet sau ve microservices va distributed systems."
)


def _make_sample_pdf_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(50, 750, text)
    c.save()
    return buf.getvalue()


def _make_sample_docx_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph(text)
    doc.save(buf)
    return buf.getvalue()


def test_extract_text_from_pdf_with_content_marks_parsed():
    pdf_bytes = _make_sample_pdf_bytes(SAMPLE_JD_TEXT)
    text, status = extract_text_from_pdf(pdf_bytes)
    assert "Backend Engineer" in text
    assert status == "parsed"


def test_extract_text_from_pdf_empty_marks_needs_review():
    pdf_bytes = _make_sample_pdf_bytes("")
    _, status = extract_text_from_pdf(pdf_bytes)
    assert status == "needs_review"


def test_extract_text_from_docx_with_content_marks_parsed():
    docx_bytes = _make_sample_docx_bytes(SAMPLE_JD_TEXT)
    text, status = extract_text_from_docx(docx_bytes)
    assert "Backend Engineer" in text
    assert status == "parsed"


def test_parse_jd_file_dispatches_by_extension():
    docx_bytes = _make_sample_docx_bytes(SAMPLE_JD_TEXT)
    _, status = parse_jd_file("jd.docx", docx_bytes)
    assert status == "parsed"


def test_parse_jd_file_rejects_unsupported_extension():
    try:
        parse_jd_file("jd.txt", b"some content")
        assert False, "Phải raise ValueError cho định dạng không hỗ trợ"
    except ValueError as e:
        assert "khong ho tro" in str(e).lower() or "không hỗ trợ" in str(e)