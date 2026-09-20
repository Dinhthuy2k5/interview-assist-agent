---
name: project-development
description: Use this skill when developing, reviewing, debugging, testing, refactoring, or designing features for the Interview Assist Agent project. Follows the project's exact architecture, conventions, and compliance rules.
---

# Interview Assist Agent - Development Skill

## Non-Negotiable Hard Rules
1. **HITL (Human-in-the-Loop)**: AI (Aggregation / Suggestion Agent) TUYỆT ĐỐI KHÔNG ghi vào `session_decision`. Chỉ role `council` mới được ghi quyết định tuyển dụng cuối cùng. Toàn bộ gợi ý AI chỉ mang tính tham vấn.
2. **Privacy & Anonymity**:
   - Interviewer chỉ có quyền xem/sửa note của chính mình.
   - Note xuất ra cho Council phải ẩn danh với nhãn cố định (`Người phỏng vấn 1`, `Người phỏng vấn 2`,...).
3. **Compliance Filter**: Mọi câu hỏi do LLM sinh ra bắt buộc phải đi qua `sensitive_filter.py` trước khi lưu vào DB hoặc hiển thị cho người dùng.
4. **Stateless Backend**: Backend FastAPI hoàn toàn stateless; không lưu state trong in-memory tiến trình; chia sẻ cache, session, rate-limit qua Redis (`redis:6379`).
5. **Security & Cyber Defense**:
   - Chống IDOR: Mọi API đọc/ghi session, note, ứng viên phải kiểm tra tính sở hữu (`user_id == current_user.id`) hoặc quyền được gán, không tin cậy ID client gửi lên.
   - Chống Injection: 100% validate qua Pydantic v2, truy vấn bằng SQLAlchemy ORM (cấm ghép chuỗi raw SQL), React escape output (cấm `dangerouslySetInnerHTML`).
   - File Upload & MinIO: Bắt buộc kiểm tra Magic Bytes (File Signature), giới hạn file size, lưu MinIO với key ngẫu nhiên bằng UUID (chống Path Traversal), bucket private.
   - LLM Security: Sanitize và phân tách delimiter rõ ràng với dữ liệu CV/audio phiên âm (chống Prompt Injection), không gửi PII nhạy cảm ra LLM bên ngoài, áp dụng token budget và timeout.
   - Secrets & Network: Không hardcode credentials/API keys trong code/git; port 8000/db/redis/minio không expose ra host; rate-limit qua Redis trên các endpoint nhạy cảm.
6. **Quality Gates**: Mọi thay đổi code bắt buộc chạy và pass `ruff check` + `pytest tests/` (backend) và `npm run build` (frontend).

## Architecture & Code Conventions

### Backend (FastAPI + Python 3.11)
- **Folder structure**:
  - `app/api`: Router endpoints, request parsing, HTTP status codes, dependency injection (`Depends(get_db)`, `Depends(get_current_user)`).
  - `app/schemas`: Pydantic v2 schemas cho request, response và data validation.
  - `app/models`: SQLAlchemy 2.0 ORM models.
  - `app/services`: Pure business logic, orchestration giữa models, repositories và external clients.
  - `app/core`: Configuration (`pydantic-settings`), security (JWT SHA-256 hash + token rotation), database session.
  - `app/agents`: LLM prompts, agent pipelines, sensitive filters.
- **Conventions**:
  - Naming: `snake_case` cho functions, variables, modules. `PascalCase` cho classes và Pydantic models.
  - Strict type hints cho mọi hàm và tham số.
  - Tự động hóa database migration qua Alembic (`alembic revision --autogenerate -m "..."`).
  - Refresh token phải hash SHA-256 kèm cơ chế rotation.
  - Không bao giờ bind trực tiếp host port 8000 của backend trong docker-compose; mọi request từ frontend đi qua Traefik port 80.

### Frontend (React + TypeScript + Vite)
- **Conventions**:
  - Naming: `camelCase` cho functions và variables, `PascalCase` cho React components.
  - TypeScript strict typing (không dùng `any`).
  - Giao diện phân chia rõ ràng theo 3 vai trò:
    - **HR**: Quản lý chiến dịch phỏng vấn, hồ sơ ứng viên, upload CV.
    - **Interviewer**: Buổi phỏng vấn trực tiếp, ghi chú cá nhân, xem gợi ý câu hỏi từ AI.
    - **Council**: Xem đánh giá ẩn danh của các interviewer, tổng hợp đề xuất AI, đưa ra quyết định tuyển dụng cuối cùng.
  - Xử lý đầy đủ loading, error, empty states cho từng component.

### Database & Storage
- **PostgreSQL 16**: Lưu trữ quan hệ chính (users, sessions, notes, decisions). Thiết lập index cho các trường truy vấn thường xuyên.
- **Redis 7**: Cache, rate limiting, token blacklist / session validation.
- **MinIO**: S3-compatible lưu trữ file CV (PDF, DOCX).

## Testing & Verification Workflow
Trước khi hoàn tất bất kỳ thay đổi nào:
1. Chạy lint backend: `ruff check .` (sửa triệt để mọi cảnh báo).
2. Chạy test backend: `pytest tests/` (đảm bảo pass 100%).
3. Chạy build frontend: `npm run build` (trong thư mục `frontend/`, đảm bảo không lỗi TypeScript).
4. Giữ nguyên docstrings, comments giải thích kiến trúc và type annotations.

## Lessons Learned Checklist
- [x] Không bind trực tiếp host port vào service backend khi hỗ trợ scale ngang với Traefik.
- [x] Luôn trỏ `REDIS_URL` tới container `redis:6379` thay vì `localhost` trong môi trường Docker.
