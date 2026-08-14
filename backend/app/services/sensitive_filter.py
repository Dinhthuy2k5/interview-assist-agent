import re

# Blocklist rule-based, không phải LLM - rẻ, nhanh, kết quả xác định (deterministic),
# chạy trên MỌI câu hỏi trước khi hiện cho HR. Đây là tầng lọc đầu tiên; nếu sau này
# phát hiện blocklist bỏ sót nhiều trường hợp, bổ sung thêm 1 lớp LLM classifier
# nhẹ ở phía sau (chưa cần thiết ở scope hiện tại).
#
# Nhóm dựa theo các chủ đề luật lao động Việt Nam hạn chế nhà tuyển dụng hỏi trong
# phỏng vấn: hôn nhân/gia đình, tôn giáo, tuổi, giới tính/dân tộc, sức khỏe/thai sản.
SENSITIVE_PATTERNS: dict[str, list[str]] = {
    "hôn nhân/gia đình": [
        r"\bkết hôn\b", r"\bchồng\b", r"\bvợ\b", r"\bcon cái\b", r"\bly hôn\b",
        r"\bđộc thân\b", r"\bgia đình\b",
    ],
    "tôn giáo": [r"\btôn giáo\b", r"\bđạo\b", r"\btín ngưỡng\b"],
    "tuổi": [r"\bbao nhiêu tuổi\b", r"\bnăm sinh\b", r"\btuổi tác\b"],
    "giới tính/dân tộc": [r"\bgiới tính\b", r"\bdân tộc\b", r"\bxu hướng tính dục\b"],
    "sức khỏe/thai sản": [
        r"\bmang thai\b", r"\bthai sản\b", r"\bbệnh (?:mãn tính|nền)\b", r"\bsức khỏe sinh sản\b",
    ],
}

_COMPILED = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]
    for category, patterns in SENSITIVE_PATTERNS.items()
}


def check_sensitive_content(text: str) -> tuple[bool, str | None]:
    """Trả về (is_flagged, reason). reason nêu nhóm chủ đề vi phạm, không trích
    dẫn nguyên văn từ khóa (tránh biến message lỗi thành hướng dẫn né filter)."""
    for category, patterns in _COMPILED.items():
        for pattern in patterns:
            if pattern.search(text):
                return True, f"Câu hỏi chạm nhóm chủ đề nhạy cảm: {category}"
    return False, None