# Interview Assist Agent (IAA)

AI Agent hỗ trợ phỏng vấn & tổng hợp đánh giá ứng viên.


## Mục tiêu
Sinh câu hỏi phỏng vấn theo JD & cấp độ, hỗ trợ ghi note/chấm điểm theo khung năng lực
trong buổi phỏng vấn, tổng hợp đánh giá từ nhiều người phỏng vấn thành khuyến nghị.
Quyết định tuyển dụng cuối cùng luôn do con người (HITL bắt buộc).

## Cấu trúc dự án
- `backend/` — FastAPI service (JD Parse, Question Gen Agent, Session/Note, Aggregation Agent, Decision)
- `frontend/` — React + TypeScript (HR Dashboard, Interviewer Console, Council Review)
- `docs/` — kiến trúc, data model, Architecture Decision Records (ADR), sprint notes

## Tài liệu
- [Kiến trúc hệ thống](docs/architecture.md)
- [Data Model](docs/data-model.md)
- [Architecture Decision Records](docs/decisions/)

## Trạng thái
🚧 Đang phát triển — Sprint 0 (setup nền tảng)