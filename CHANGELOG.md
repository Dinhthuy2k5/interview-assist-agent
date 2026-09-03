# Changelog

Ghi lại theo sprint, không theo từng commit riêng lẻ — mỗi mục là 1 khả năng hoàn
chỉnh đã có migration + API + test (nếu là backend) hoặc UI thật (nếu là frontend).

## Sprint 6 — Decision Service + RBAC hoàn chỉnh + Audit Log

**Backend**
- `session_decision`: Hội đồng ghi quyết định cuối (hired/rejected/on_hold + lý
  do bắt buộc), **append-only** — không sửa/xoá lịch sử, `decided_by` hiện tên
  thật (khác `interviewer_note` ẩn danh).
- `audit_log`: ghi đăng nhập (thành công/thất bại), tạo/sửa tài khoản, tạo quyết
  định. Chỉ `hr_admin` đọc được.
- Rà soát RBAC toàn hệ thống theo bảng actor gốc — xác nhận các endpoint đã đúng
  từ các lần fix tích luỹ Sprint 3-5.
- Council được cấp quyền xem `GET /sessions/{id}` (câu hỏi đã hỏi) — tách riêng
  `require_session_read_access` khỏi `require_session_access` (đổi status/
  transcript) để không vô tình cấp thừa quyền khi mở rộng quyền xem.

**Frontend**
- `DecisionPanel` dùng chung: Council ghi quyết định, HR chỉ xem — lịch sử
  append-only thu gọn trong `<details>`.
- `SessionQuestionsPanel`: Council xem câu hỏi đã hỏi.
- Trang "Nhật ký hệ thống" (HR Admin) — bảng audit log.
- `SessionManagePage`/`CouncilReportPage` đổi sang tab con trong cột chi tiết
  (Transcript/Báo cáo/Quyết định — Báo cáo/Câu hỏi/Quyết định) để tránh nhồi
  nhiều panel dài trong 1 cột.

## Sprint 5 — Aggregation Service

**Backend**
- `aggregation_report`: rule-based variance check (chênh ≥2 điểm) chạy trước,
  embedding similarity check (sentence-transformers, lazy import) chỉ chạy khi
  rule-based không flag, LLM semantic check chỉ chạy khi có conflict — kiểm soát
  chi phí đúng thiết kế gốc.
- Label ẩn danh interviewer (`build_interviewer_labels`) gán 1 lần cho cả
  session, dùng chung mọi criterion — tránh 1 nhãn trỏ 2 người khác nhau.
- `missing_interviewer_labels` thay vì đếm số — đúng yêu cầu "hiện rõ thiếu ai".
- `GET /sessions/{id}/notes`: HR/Council xem note gốc khi cần đối chiếu.
- Tách `app/services/llm_client.py` dùng chung cho Question Gen và Aggregation —
  cả 2 đều theo `settings.llm_provider` (mock/anthropic/groq), không hard-code
  provider nào.

**Frontend**
- `AggregationPanel`: HR trigger tổng hợp, Council chỉ đọc — hiện điểm trung
  bình có trọng số, khuyến nghị, conflict theo từng tiêu chí, note gốc.

## Sprint 4 — Transcript Service (batch STT)

**Backend**
- `transcript`: 1 audio/session, xử lý đồng bộ (blocking) trong request — đúng
  tính năng batch, không real-time. `faster-whisper` lazy import, tách
  `optional-dependencies[stt]` riêng để không kéo vào cài đặt dev/test hàng ngày.
- Giới hạn dung lượng audio (300MB) — tránh 1 file quá dài chiếm dụng worker.
- Cho phép upload lại khi `status="failed"` (retry), chặn khi đã
  `completed`/`processing`.
- `retention_expiry` set ngay lúc tạo theo NFR bảo mật dữ liệu ứng viên.

**Frontend**
- `TranscriptPanel`: upload audio, hiện trạng thái/transcript, tải lại khi
  failed, hiện ngày hết hạn bản ghi.

## Sprint 3 — Auth (JWT + RBAC) + Session & Note Service

**Backend**
- `user` + JWT login (`python-jose`, bcrypt) — không có endpoint tự đăng ký, chỉ
  `hr_admin` tạo được tài khoản. Script `create_admin.py` tạo `hr_admin` đầu
  tiên khi mới deploy.
- `interview_session`, `session_interviewer`, `interviewer_note`: HR tạo session
  + gán interviewer, mỗi interviewer chỉ ghi/xem note của chính mình (đảm bảo
  đánh giá độc lập, đúng nguyên tắc công bằng).
- `require_role`/`require_session_access` — áp dụng phân quyền cho toàn bộ
  router đã có từ trước (jobs, frameworks, questions).

**Frontend**
- Login page, `AuthContext`, điều hướng theo role.
- Trang quản lý tài khoản (HR Admin).
- Giao diện Interviewer dạng thẻ lật từng tiêu chí, ghi note + chấm điểm.

## Sprint 2 — Question Gen Agent

**Backend**
- Sinh câu hỏi theo JD + criterion + rubric, qua Sensitive-Attribute Filter
  (chặn câu hỏi động chạm hôn nhân/tôn giáo/tuổi/thai sản...).
- HITL: câu hỏi mặc định `is_approved=False`, HR phải duyệt trước khi dùng.
- Đa provider LLM (Anthropic/Groq/mock) — tránh phụ thuộc 1 nhà cung cấp trả phí
  khi dev/test.

**Frontend**
- Trang sinh + duyệt câu hỏi, sửa nội dung, hiện rubric dạng bảng.

## Sprint 1 — JD Parse Service

**Backend**
- Upload JD (PDF/docx), trích xuất text, đánh dấu `needs_review` nếu extraction
  không chắc chắn — HR sửa tay trước khi dùng cho bước sinh câu hỏi.

**Frontend**
- Trang tạo Job, tải lên JD, xem/sửa text đã trích xuất.

## Sprint 0 — Nền tảng

- Cấu trúc repo (backend FastAPI + frontend React/Vite), CI (ruff + pytest,
  eslint + build), Docker Compose (Postgres, MinIO, backend, frontend).
- `competency_framework`, `criterion` — HR định nghĩa khung năng lực dùng chung
  cho nhiều vị trí.