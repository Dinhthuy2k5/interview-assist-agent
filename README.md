# Interview Assist Agent (IAA)

AI Agent hỗ trợ phỏng vấn & tổng hợp đánh giá ứng viên.
Đề tài 113 | Hỗ trợ – Back office | BO-17

## Mục tiêu

Sinh câu hỏi phỏng vấn theo JD & cấp độ, hỗ trợ ghi note/chấm điểm theo khung năng lực
trong buổi phỏng vấn, tổng hợp đánh giá từ nhiều người phỏng vấn thành khuyến nghị.
Quyết định tuyển dụng cuối cùng luôn do con người (HITL bắt buộc).

## Trạng thái hiện tại

🚧 Đang phát triển — **hoàn thành Sprint 0-3** (setup, JD Parse, Question Gen, Session & Note).
Xem chi tiết từng sprint: [CHANGELOG.md](CHANGELOG.md).

## Vai trò & tính năng đã có

| Vai trò | Tính năng |
|---|---|
| **HR Admin** | Tạo/quản lý Khung năng lực · Tải lên JD, xem/sửa nội dung đã trích xuất · Quản lý vị trí tuyển dụng (hạn nộp hồ sơ, đóng/mở tuyển) · Sinh & duyệt câu hỏi phỏng vấn · Tạo phiên phỏng vấn (gán interviewer) · Quản lý tài khoản người dùng |
| **Interviewer** | Xem phiên phỏng vấn được gán · Ghi note + chấm điểm (1-5) theo từng tiêu chí trong lúc phỏng vấn · Không thấy note của interviewer khác cùng phiên (đảm bảo đánh giá độc lập) |
| **Hội đồng (Council)** | Chưa có tính năng — dự kiến ở sprint sau (tổng hợp đánh giá đa người phỏng vấn + quyết định cuối) |

Không có endpoint tự đăng ký — tài khoản chỉ được tạo bởi HR Admin.

## Cấu trúc dự án

```
backend/    FastAPI — JD Parse, Question Gen Agent, Session & Note, Auth/RBAC
frontend/   React + TypeScript — giao diện tách riêng theo từng role
docs/       Kiến trúc, data model, ADR, sprint notes
```

## Chạy thử (local, Docker)

```bash
cp .env.example .env
```

Trong `.env`, cần điền/đổi:
- `ANTHROPIC_API_KEY` (hoặc `GROQ_API_KEY` nếu dùng `LLM_PROVIDER=groq`; dùng
  `LLM_PROVIDER=mock` để dev không tốn phí)
- `JWT_SECRET` — **bắt buộc đổi** thành chuỗi random dài, không giữ giá trị mặc định
  (`python -c "import secrets; print(secrets.token_hex(32))"`)

```bash
docker-compose up --build
docker-compose exec backend alembic upgrade head
```

- Backend: http://localhost:8000 (Swagger: `/docs`)
- Frontend: http://localhost:5173
- MinIO console: http://localhost:9001

Tài khoản đầu tiên phải tạo trực tiếp qua DB hoặc script seed (chưa có endpoint
tự đăng ký) — sau đó dùng tài khoản `hr_admin` đó để tạo các tài khoản còn lại
qua `POST /users`.

## Tech stack

| Layer | Công nghệ |
|---|---|
| Backend | FastAPI (Python 3.11), SQLAlchemy 2.0, Alembic |
| Frontend | React + TypeScript (Vite) |
| Database | PostgreSQL 16 |
| Object Storage | MinIO (S3-compatible) |
| LLM | Claude API / Groq (multi-provider, có chế độ mock cho dev) |
| Auth | JWT (HS256) + bcrypt, RBAC theo role (hr_admin/interviewer/council) |
| CI/CD | GitHub Actions (lint + test riêng backend/frontend) |
| Containerize | Docker + docker-compose |

## Tài liệu

- [Kiến trúc hệ thống](docs/architecture.md)
- [Data Model](docs/data-model.md)
- [Architecture Decision Records](docs/decisions/)
- [Changelog theo sprint](CHANGELOG.md)

## Testing

```bash
cd backend
pip install -e ".[dev]"
ruff check app tests alembic
PYTHONPATH=. pytest tests/ -v
```

```bash
cd frontend
npm install
npx eslint .
npm run build
```

## Git tag / release theo sprint

```bash
git tag -a v0.1.0 -m "Sprint 0-1: nền tảng + JD Parse Service"
git tag -a v0.2.0 -m "Sprint 2: Question Gen Agent + Sensitive Filter"
git tag -a v0.3.0 -m "Sprint 3: Auth + Session & Note Service"
git push origin --tags
```