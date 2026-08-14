from app.services.sensitive_filter import check_sensitive_content


def test_flags_marriage_related_question():
    flagged, reason = check_sensitive_content("Bạn đã kết hôn chưa và có con cái không?")
    assert flagged is True
    assert "hôn nhân" in reason.lower()


def test_flags_religion_related_question():
    flagged, _ = check_sensitive_content("Bạn theo tôn giáo nào?")
    assert flagged is True


def test_flags_pregnancy_related_question():
    flagged, _ = check_sensitive_content("Bạn có đang mang thai không?")
    assert flagged is True


def test_does_not_flag_normal_technical_question():
    flagged, reason = check_sensitive_content(
        "Bạn từng debug race condition trong hệ thống dùng Kafka như thế nào?"
    )
    assert flagged is False
    assert reason is None