# Changelog

Ghi lại theo sprint, không theo ngày lẻ tẻ — mỗi sprint là 1 mốc có ý nghĩa nghiệp vụ,
khớp với tag git tương ứng (xem hướng dẫn tag ở cuối README).

## Sprint 3 — Session & Note Service (role Interviewer)

- **Auth thật:** User model (hr_admin/interviewer/council), JWT (HS256) + bcrypt,
  `require_role` dependency chặn endpoint theo role
- **Session:** HR tạo phiên phỏng vấn (job, ứng viên, gán interviewer), interviewer
  xem phiên của mình, ghi note + chấm điểm (1-5) theo từng tiêu chí
- **Privacy:** mỗi interviewer chỉ thấy note của chính mình trong cùng 1 phiên —
  tránh ghi note theo nhau trước khi có bước tổng hợp
- **Frontend:** giao diện tách theo role (nav khác nhau cho HR/Interviewer/Council),
  luồng phỏng vấn dạng thẻ (1 câu/lần), rubric hiển thị dạng bảng dễ đọc

## Sprint 2 — Question Gen Agent + Sensitive-Attribute Filter

- Agent sinh 1 câu hỏi/tiêu chí dựa trên JD đã xác nhận, hỗ trợ nhiều LLM provider
  (Anthropic, Groq, mock cho dev) để kiểm soát chi phí
- Sensitive-Attribute Filter (blocklist rule-based): chặn câu hỏi chạm nhóm chủ đề
  bị luật lao động hạn chế hỏi (hôn nhân/gia đình, tôn giáo, tuổi, giới tính/dân tộc,
  sức khỏe/thai sản) — re-check lại mỗi khi HR sửa nội dung câu hỏi
- HITL: câu hỏi mặc định chưa duyệt (`is_approved=false`), không thể duyệt câu đang
  bị đánh dấu nhạy cảm (chặn ở tầng API, không chỉ UI)
- `LlmUsageLog` ghi token + chi phí thật mỗi lần gọi LLM
- Frontend: UI tạo Khung năng lực, duyệt/sửa câu hỏi

## Sprint 1 — JD Parse Service

- Upload JD (PDF/docx) → extract text (pdfplumber/python-docx), đánh giá độ tin cậy
  (`parsed`/`needs_review`), lưu file gốc vào MinIO
- CRUD tối thiểu cho Competency Framework (mỗi Job bắt buộc gắn 1 framework)
- Frontend: form upload JD, xem/sửa nội dung đã trích xuất

## Sprint 0 — Nền tảng

- Cấu trúc project (backend FastAPI + frontend React/Vite), docker-compose
  (Postgres, MinIO, backend, frontend)
- Alembic + migration đầu tiên (CompetencyFramework, Criterion, Job, Question)
- CI/CD: GitHub Actions cho backend (ruff + pytest) và frontend (eslint + build)
- `docs/architecture.md`, `docs/data-model.md`, ADR 0001 (tách Aggregation Service
  và Decision Service để enforce HITL ở tầng kiến trúc)