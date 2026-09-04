# Data Model

Trạng thái hiện tại: **đã implement đầy đủ qua migration thật tới Sprint 6** — toàn
bộ bảng trong Phân tích ban đầu đều đã có migration + model + API + test, không
còn bảng nào ở trạng thái kế hoạch. MVP hoàn thiện.

## `user`
Tài khoản đăng nhập. Không có endpoint tự đăng ký — chỉ `hr_admin` tạo được tài
khoản (hoặc script `python -m app.scripts.create_admin` để tạo `hr_admin` đầu
tiên khi mới deploy).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| email | String(255), unique | |
| full_name | String(255) | |
| password_hash | String(255) | bcrypt |
| role | String(20) | hr_admin / interviewer / council |
| is_active | Boolean, default true | HR khoá tài khoản mà không xoá dữ liệu liên quan |
| created_at / updated_at | DateTime | |

## `refresh_token` (sau MVP)
Cho phép cấp lại `access_token` mới mà không cần đăng nhập lại, đồng thời là cơ
chế **duy nhất** thực sự "đăng xuất" được — `access_token` (JWT) tự thân không
lưu trạng thái, không thể thu hồi giữa chừng trước khi hết hạn.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → user, CASCADE | |
| token_hash | String(64), unique, index | SHA-256 — lưu hash, không lưu token gốc (cùng nguyên tắc `password_hash`) |
| expires_at | DateTime(timezone=True), NOT NULL | |
| revoked_at | DateTime(timezone=True), nullable | Khác `None` = đã vô hiệu hoá (logout, hoặc đã "xoay vòng" sau 1 lần refresh) |
| created_at / updated_at | DateTime | |

**Rotation**: mỗi lần refresh thành công, token cũ bị revoke ngay, cấp token mới
— 1 refresh token chỉ dùng được đúng 1 lần. Nếu 1 token đã `revoked_at` mà vẫn bị
dùng lại — dấu hiệu bị đánh cắp — hệ thống revoke **toàn bộ** token còn sống của
user đó, không chỉ riêng token bị dùng lại.

## `competency_framework`, `criterion`, `question`, `llm_usage_log`

Không đổi so với Sprint 0-2, xem lịch sử file này qua git nếu cần đối chiếu chi tiết
từng cột. `criterion.weight` là trọng số **tương đối** (không phải thang 0-100) —
tính % hiển thị luôn phải chia cho tổng weight của cả framework, không hiển thị
giá trị thô.

## `job`

Bổ sung so với Sprint 1: `application_deadline`, `is_closed` (quản lý vòng đời tuyển
dụng), `created_by` lấy từ `User.full_name` của người gọi API đã xác thực (không
phải string tự do client gửi lên).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| application_deadline | Date, nullable | Hạn nộp hồ sơ - null nghĩa là không giới hạn |
| is_closed | Boolean | HR đóng tuyển tay, độc lập với hạn nộp |

`status` ("open"/"closed") **không lưu cột riêng** — tính động ở tầng schema
(`JobResponse.status`) từ `application_deadline`/`is_closed`, tránh lệch dữ liệu
nếu quên chạy job cập nhật khi qua hạn.

## `interview_session`
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

## `session_interviewer`
Bảng liên kết N-N: 1 session có nhiều interviewer tham gia độc lập.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_session, CASCADE | |
| interviewer_id | UUID FK → user | |
| Unique constraint | (session_id, interviewer_id) | Không gán trùng 1 interviewer 2 lần |

## `interviewer_note`
Note + điểm của 1 interviewer cho 1 criterion trong 1 session — **riêng tư giữa các
interviewer**, chỉ chính chủ mới xem được note của mình qua API session detail.
HR/Council xem được qua endpoint riêng (`GET /sessions/{id}/notes`) sau khi đã có
report tổng hợp, hiển thị kèm nhãn ẩn danh ổn định (không phải tên thật).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_session, CASCADE | |
| interviewer_id | UUID FK → user | |
| criterion_id | UUID FK → criterion | |
| score | Integer, nullable | 1-5 |
| note_text | Text, nullable | |
| Unique constraint | (session_id, interviewer_id, criterion_id) | PUT lặp lại là upsert, không tạo trùng |

## `transcript` (Sprint 4)
Bản ghi âm + text đã transcribe cho 1 session — 1 session chỉ có 1 transcript
(mic ghi cả buổi, dùng chung cho mọi interviewer tham khảo).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_session, CASCADE, **unique** | 1 transcript/session |
| audio_file_path | String(512) | Object key trong MinIO |
| text | Text, nullable | |
| status | String(20), default "pending" | pending / processing / completed / failed |
| retention_expiry | DateTime(timezone=True), NOT NULL | Set ngay lúc tạo, mặc định 180 ngày (NFR bảo mật dữ liệu ứng viên) |

Cho phép **ghi đè khi `status="failed"`** (retry), nhưng **chặn** ghi đè khi đã
`completed`/`processing` — coi audio đã xử lý xong như bằng chứng gốc, không cho
xoá âm thầm.

## `aggregation_report` (Sprint 5)
Kết quả tổng hợp đánh giá đa người phỏng vấn cho 1 session — **thuần advisory**,
không phải quyết định cuối (xem [ADR 0001](decisions/0001-microservice-boundaries-and-hitl-enforcement.md)).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_session, CASCADE, **unique** | Upsert khi tổng hợp lại - không phải bằng chứng gốc như Transcript |
| per_criterion_summary | JSON | `list[{criterion_id, criterion_name, scores, average, has_conflict, conflict_type, semantic_note, missing_interviewer_labels}]` |
| overall_score | Numeric(3,2), nullable | Điểm trung bình có trọng số, null nếu chưa có note nào |
| overall_recommendation | String(50) | "Đề xuất tuyển" / "Cần thảo luận thêm" / "Không đề xuất" / "Chưa đủ dữ liệu" — CHỈ tư vấn |
| rationale_trace | Text, NOT NULL | Narrative giải thích - bắt buộc, không được chỉ trả số trần trụi |

`missing_interviewer_labels` (không phải count) — đúng yêu cầu thiết kế "hiện rõ
thiếu ai" khi không bắt buộc đủ 100% interviewer nộp note. Label ẩn danh
(`"Người phỏng vấn N"`) được gán **1 lần duy nhất cho cả session**, dùng chung cho
mọi criterion — tránh tình trạng cùng 1 nhãn trỏ tới 2 người khác nhau giữa các
tiêu chí nếu ai đó bỏ sót note ở 1 criterion.

## `session_decision` (Sprint 6)
Quyết định tuyển dụng **cuối cùng** do Hội đồng ghi — authoritative, khác hẳn
`aggregation_report`.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → interview_session, CASCADE | **Không unique** - append-only |
| decided_by | UUID FK → user | Hiện **tên thật**, không ẩn danh như InterviewerNote |
| decision | String(20) | hired / rejected / on_hold |
| rationale | Text, NOT NULL | Bắt buộc, không được để trống |
| created_at / updated_at | DateTime | |

**APPEND-ONLY**: mỗi lần Council quyết định (hoặc đổi ý) tạo dòng **mới**, không
sửa/xoá dòng cũ — bản thân bảng này chính là audit trail cho quyết định tuyển
dụng. "Quyết định hiện tại" = dòng mới nhất theo `created_at`.

## `audit_log` (Sprint 6)
Nhật ký hành động nhạy cảm không thuộc về 1 service nghiệp vụ cụ thể.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| actor_id | UUID FK → user, nullable | null cho `login_failed` chưa xác định được actor |
| action | String(50) | login_success / login_failed / logout / refresh_token_reuse_detected / user_created / user_updated / decision_created |
| target_type / target_id | String, nullable | |
| detail | Text, nullable | Không bao giờ ghi password |
| created_at | DateTime(timezone=True) | **Không có `updated_at`** - log bất biến, không ai được sửa 1 dòng đã ghi |

Chỉ `hr_admin` đọc được qua `GET /audit-log`.