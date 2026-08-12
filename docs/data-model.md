# Data Model

Trạng thái hiện tại: 5 bảng đã có migration (`e2614e6b7131`, `b54bb688f164`).
Các bảng `Interview Session`, `Interviewer Note`, `Transcript`, `Aggregation Report`,
`Decision` ở Phân tích/Thiết kế ban đầu **chưa có migration** — sẽ thêm ở các sprint
tương ứng (Sprint 3-6), tài liệu này cập nhật dần theo tiến độ thật.

## Đã implement

### `competency_framework`
Khung năng lực — nguồn sự thật duy nhất cho việc sinh câu hỏi và chấm điểm.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| name | String(255) | |
| description | Text, nullable | |
| created_at / updated_at | DateTime | |

### `criterion`
Một tiêu chí cụ thể trong khung năng lực (VD "Problem solving").

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| framework_id | UUID FK → competency_framework, CASCADE | |
| name | String(255) | |
| weight | Numeric(3,2), default 1.0 | |
| scoring_rubric | Text, NOT NULL | Mô tả từng mức điểm 1-5 |
| created_at / updated_at | DateTime | |

### `job`
Một vị trí tuyển dụng.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| title | String(255) | |
| level | String(50) | fresher/junior/senior |
| jd_file_path | String(512) | Object key trong MinIO |
| jd_text | Text, nullable | Kết quả parse, HR sửa được |
| jd_parse_status | String(20), default "pending" | pending/parsed/needs_review |
| framework_id | UUID FK → competency_framework | |
| created_by | String(255) | |
| created_at / updated_at | DateTime | |

### `question`
Câu hỏi phỏng vấn — **bắt buộc** gắn với 1 criterion.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| job_id | UUID FK → job, CASCADE | |
| criterion_id | UUID FK → criterion, NOT NULL | Enforce trace-về-rubric ở tầng DB |
| content | Text, NOT NULL | |
| rationale | Text, NOT NULL | Vì sao câu hỏi đo được tiêu chí đó |
| generated_by | String(20), default "agent" | agent / human_edited |
| is_sensitive_flagged | Boolean, default false | Kết quả Sensitive-Attribute Filter |
| sensitive_flag_reason | Text, nullable | |
| is_approved | Boolean, default false | HR phải duyệt trước khi dùng |
| created_at / updated_at | DateTime | |

### `llm_usage_log`
Log mỗi lần gọi LLM — theo dõi chi phí thực tế.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| service | String(50) | question_gen / aggregation_semantic_check / ... |
| tokens_in | Integer | |
| tokens_out | Integer | |
| cost_estimate | Numeric(10,6) | USD |
| timestamp | DateTime | Bản ghi bất biến, không có updated_at |

## Chưa implement (kế hoạch, sẽ cập nhật khi có migration thật)

- `interview_session` — id, job_id, candidate_id, interviewers[], scheduled_at, status
- `interviewer_note` — id, session_id, interviewer_id, criterion_id, score, note_text, source (manual/ai_assisted)
- `transcript` — id, session_id, raw_audio_ref, text, timestamps, retention_expiry
- `aggregation_report` — id, session_id, per_criteria_summary[], conflict_flags[], overall_recommendation, rationale_trace
- `decision` — id, session_id, decided_by, final_decision, decided_at (bảng duy nhất Decision Service được ghi)