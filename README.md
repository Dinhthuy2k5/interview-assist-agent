# Interview Assist Agent (IAA)

AI Agent hỗ trợ phỏng vấn & tổng hợp đánh giá ứng viên.
Đề tài 113 | Hỗ trợ – Back office | BO-17

## Mục tiêu

Sinh câu hỏi phỏng vấn theo JD & cấp độ, hỗ trợ ghi note/chấm điểm theo khung năng lực
trong buổi phỏng vấn, tổng hợp đánh giá từ nhiều người phỏng vấn thành khuyến nghị.
Quyết định tuyển dụng cuối cùng luôn do con người (HITL bắt buộc).

## Trạng thái hiện tại

✅ **MVP hoàn thiện — Sprint 0-6.** Toàn bộ service trong Phân tích ban đầu (JD
Parse, Question Gen, Session & Note, Transcript/STT, Aggregation, Decision) đều
đã có migration + API + test thật, cùng RBAC đầy đủ theo 3 role. Xem chi tiết
từng sprint: [CHANGELOG.md](CHANGELOG.md).

## Vai trò & tính năng

| Vai trò | Tính năng |
|---|---|
| **HR Admin** | Tạo/quản lý Khung năng lực · Tải lên JD, xem/sửa nội dung đã trích xuất · Quản lý vị trí tuyển dụng (hạn nộp hồ sơ, đóng/mở tuyển) · Sinh & duyệt câu hỏi phỏng vấn · Tạo phiên phỏng vấn (gán interviewer) · Xem transcript, báo cáo tổng hợp, quyết định của từng phiên (chỉ đọc) · Quản lý tài khoản người dùng · Xem nhật ký hệ thống (audit log) |
| **Interviewer** | Xem phiên phỏng vấn được gán · Ghi note + chấm điểm (1-5) theo từng tiêu chí trong lúc phỏng vấn, tham khảo transcript · Không thấy note của interviewer khác cùng phiên (đảm bảo đánh giá độc lập) |
| **Hội đồng (Council)** | Xem danh sách phiên đã tổng hợp · Xem báo cáo tổng hợp đa người phỏng vấn (điểm trung bình, khuyến nghị, điểm không đồng nhất giữa các interviewer) · Xem note gốc và câu hỏi đã hỏi khi cần đối chiếu · **Ghi quyết định tuyển dụng cuối cùng** (hired/rejected/on_hold, kèm lý do bắt buộc) — quyết định luôn do người, không bao giờ tự động |

Không có endpoint tự đăng ký — tài khoản chỉ được tạo bởi HR Admin.

## Nguyên tắc thiết kế cốt lõi (HITL)

Aggregation Service (AI tổng hợp đánh giá) **không có quyền ghi** vào bảng quyết
định — chỉ Hội đồng, qua Decision Service, mới ghi được quyết định cuối cùng. Đây
là ràng buộc ở tầng data model/kiến trúc, không chỉ là quy ước. Xem
[ADR 0001](docs/decisions/0001-microservice-boundaries-and-hitl-enforcement.md).

## Cấu trúc dự án

```
backend/    FastAPI — JD Parse, Question Gen, Session & Note, Transcript,
            Aggregation, Decision, Auth/RBAC, Audit Log
frontend/   React + TypeScript — giao diện tách riêng theo từng role
docs/       Kiến trúc, data model, ADR, sprint notes
```

## Chạy thử (local, Docker)

```bash
cp .env.example .env
```

Trong `.env`, cần điền/đổi:
- `ANTHROPIC_API_KEY` (hoặc `GROQ_API_KEY` nếu dùng `LLM_PROVIDER=groq` — free
  tier, khuyến nghị cho dev; `LLM_PROVIDER=mock` để dev không gọi LLM thật)
- `JWT_SECRET` — **bắt buộc đổi** thành chuỗi random dài, không giữ giá trị mặc
  định (`python -c "import secrets; print(secrets.token_hex(32))"`)
- `JWT_EXPIRE_MINUTES` (mặc định 30) — thời hạn `access_token`, cố tình ngắn vì
  không thể thu hồi giữa chừng
- `REFRESH_TOKEN_EXPIRE_DAYS` — thời hạn `refresh_token` (dùng để cấp lại
  `access_token` qua `POST /auth/refresh`, có rotation + phát hiện reuse)

```bash
docker compose up --build
docker compose exec backend alembic upgrade head
```

- Backend: http://localhost:8000 (Swagger: `/docs`)
- Frontend: http://localhost:5173
- MinIO console: http://localhost:9001

**Tạo tài khoản HR Admin đầu tiên** (không có endpoint tự đăng ký, cần bước này
1 lần khi mới deploy):
```bash
docker compose exec backend python -m app.scripts.create_admin
```
Sau đó dùng tài khoản `hr_admin` đó đăng nhập, tạo các tài khoản `interviewer`/
`council` còn lại qua trang "Người dùng" (hoặc `POST /users`).

**Tính năng transcript (STT)** cần cài thêm `faster-whisper` (đã có sẵn trong
Docker image qua `pip install -e ".[stt]"` — build lần đầu sẽ chậm hơn vì
`ctranslate2` khá nặng). Model tự tải từ HuggingFace Hub lần chạy đầu tiên, cần
mạng ra ngoài.

## Tech stack

| Layer | Công nghệ |
|---|---|
| Backend | FastAPI (Python 3.11), SQLAlchemy 2.0, Alembic |
| Frontend | React + TypeScript (Vite) |
| Database | PostgreSQL 16 |
| Object Storage | MinIO (S3-compatible) |
| STT | faster-whisper (self-host, batch) |
| Embedding | sentence-transformers (self-host) — pre-check trước khi gọi LLM |
| LLM | Claude API / Groq (multi-provider qua `LLM_PROVIDER`, có chế độ mock cho dev) |
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
git tag -a v0.4.0 -m "Sprint 4: Transcript Service (batch STT)"
git tag -a v0.5.0 -m "Sprint 5: Aggregation Service"
git tag -a v0.6.0 -m "Sprint 6: Decision Service + RBAC hoàn chỉnh + Audit Log"
git tag -a v1.0.0-mvp -m "MVP hoàn thiện - toàn bộ service theo Phân tích ban đầu"
git push origin --tags
```