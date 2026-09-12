# AGENTS.md - Chỉ dẫn dành cho AI Coding Agent

1. **Stack**: FastAPI (Python 3.11), PostgreSQL 16, Redis 7, MinIO, React 19 (TS/Vite), Docker Compose, Traefik v3.
2. **Conventions**: Python snake_case + Pydantic v2 + Ruff; TypeScript camelCase + strict typing; UI phân tách theo 3 role (HR/Interviewer/Council).
3. **Hard Rule (HITL)**: AI (Aggregation) TUYỆT ĐỐI KHÔNG ghi vào `session_decision`; chỉ role `council` mới được ghi quyết định tuyển dụng cuối cùng.
4. **Hard Rule (Privacy)**: Interviewer chỉ xem/sửa note của chính mình; note xuất ra cho Council phải ẩn danh với label cố định (`Người phỏng vấn N`).
5. **Hard Rule (Compliance)**: Mọi câu hỏi do LLM sinh ra bắt buộc qua `sensitive_filter.py` trước khi lưu hoặc hiển thị.
6. **Process (Runtime)**: Chạy full cụm qua `docker compose up --scale backend=3 -d`; API đi qua Traefik port 80; không expose trực tiếp port 8000 của backend.
7. **Process (Test & Quality)**: Luôn chạy `ruff check` + `pytest tests/` (backend) và `npm run build` (frontend) trước khi hoàn tất thay đổi.
8. **Process (Doc Integrity)**: Bảo toàn docstrings, type annotations và comments giải thích kiến trúc khi refactor.
9. **Meta Rule**: Cập nhật thêm 1 quy tắc vào mục "Lessons Learned" bên dưới mỗi khi Agent làm điều gì không nên lặp lại.
10. **State Management**: Giữ backend stateless; chia sẻ cache và rate-limit qua Redis; refresh token phải hash SHA-256 kèm cơ chế rotation.

---

## Lessons Learned (Quy tắc bổ sung khi Agent mắc lỗi)
<!-- Mỗi khi Agent làm sai hoặc có hành vi không mong muốn, bổ sung 1 gạch đầu dòng ngắn gọn vào đây -->
- [Init] Không bind trực tiếp host port vào service backend khi hỗ trợ scale ngang với Traefik.
- [Init] Luôn đảm bảo cấu hình `REDIS_URL` trỏ tới container `redis:6379` thay vì `localhost` trong Docker.
