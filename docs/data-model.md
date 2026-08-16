# Data Model

Trạng thái hiện tại: đã implement qua migration thật tới Sprint 3 (`user`,
`interview_session`, `session_interviewer`, `interviewer_note` + các bảng Sprint 0-1).
Bảng `Aggregation Report`, `Decision` từ Phân tích ban đầu **chưa có migration** —
dự kiến ở Sprint 5-6.

## Đã implement

### `user`
Tài khoản đăng nhập. Không có endpoint tự đăng ký — chỉ `hr_admin` tạo được tài khoản.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| email | String(255), unique | |
| full_name | String(255) | |
| password_hash | String(255) | bcrypt |
| role | String(20) | hr_admin / interviewer / council |
| is_active | Boolean, default true | HR khoá tài khoản mà không xoá dữ liệu liên quan |
| created_at / updated_at | DateTime | |

### `competency_framework`, `criterion`, `question`, `llm_usage_log`

Không đổi so với Sprint 0-2, xem lịch sử file này qua git nếu cần đối chiếu chi tiết
từng cột — giữ nguyên cấu trúc đã mô tả trước đó.

### `job`

Bổ sung so với Sprint 1: `application_deadline`, `is_closed` (quản lý vòng đời tuyển
dụng), `created_by` giờ lấy từ `User.full_name` của người gọi API đã xác thực
(trước đây là string tự do client gửi lên).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| application_deadline | Date, nullable | Hạn nộp hồ sơ |
| is_closed | Boolean | HR đóng tuyển tay, độc lập với hạn nộp |

### `interview_session`
1 buổi phỏng vấn cho 1 ứng viên ứng tuyển vào 1 Job.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| job_id | UUID FK → job | |
| candidate_name | String(255) | |
| candidate_info | Text, nullable | |
| scheduled_at | DateTime(timezone=True), NOT NULL | |
| status | String(20), default "scheduled" | scheduled / in_progress / completed |
| created_at / updated_at | DateTime | |

### `session_interviewer`
Bảng liên kết N-N: 1 session có nhiều interviewer tham gia độc lập.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_session, CASCADE | |
| interviewer_id | UUID FK → user | |
| Unique constraint | (session_id, interviewer_id) | Không gán trùng 1 interviewer 2 lần |

### `interviewer_note`
Note + điểm của 1 interviewer cho 1 criterion trong 1 session — **riêng tư giữa các
interviewer**, chỉ chính chủ mới xem được note của mình qua API.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_session, CASCADE | |
| interviewer_id | UUID FK → user | |
| criterion_id | UUID FK → criterion | |
| score | Integer, nullable | 1-5 |
| note_text | Text, nullable | |
| Unique constraint | (session_id, interviewer_id, criterion_id) | PUT lặp lại là upsert, không tạo trùng |

## Chưa implement

- `aggregation_report` — id, session_id, per_criteria_summary[], conflict_flags[], overall_recommendation, rationale_trace
- `decision` — id, session_id, decided_by, final_decision, decided_at (bảng duy nhất Decision Service được ghi)
- `transcript` — id, session_id, raw_audio_ref, text, timestamps, retention_expiry (Sprint 4, batch STT)