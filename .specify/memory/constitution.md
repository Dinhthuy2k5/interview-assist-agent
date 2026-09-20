# Interview Assist Agent Constitution

## Core Principles

### I. Human-In-The-Loop (HITL) Enforcement (NON-NEGOTIABLE)
AI (Aggregation / Suggestion Agent) TUYỆT ĐỐI KHÔNG ghi vào `session_decision`. Chỉ role `council` (Hội đồng tuyển dụng) mới có thẩm quyền đưa ra và lưu quyết định tuyển dụng cuối cùng. Toàn bộ đề xuất từ AI chỉ mang tính chất tham vấn, hỗ trợ quyết định.

### II. Privacy & Anonymity by Design (NON-NEGOTIABLE)
- Interviewer chỉ có quyền xem và chỉnh sửa ghi chú (interview notes) do chính mình tạo ra trong phiên phỏng vấn.
- Toàn bộ ghi chú khi tổng hợp và xuất ra cho Council bắt buộc phải được ẩn danh hóa với nhãn cố định (`Người phỏng vấn 1`, `Người phỏng vấn 2`,...) nhằm chống định kiến chủ quan giữa các giám khảo.

### III. Compliance & Sensitive Content Filtering (NON-NEGOTIABLE)
Mọi câu hỏi do LLM/AI sinh ra bắt buộc phải đi qua bộ lọc kiểm duyệt `sensitive_filter.py` trước khi lưu vào database hoặc hiển thị trên giao diện người dùng (chống câu hỏi nhạy cảm, phân biệt đối xử về giới tính, tôn giáo, vùng miền, tuổi tác, tình trạng hôn nhân).

### IV. Stateless Backend & Horizontal Scalability
Backend FastAPI phải hoàn toàn stateless để hỗ trợ scale ngang (`docker compose up --scale backend=3 -d`) phía sau Traefik v3 reverse proxy (cổng 80).
- Không lưu session state, job queue hay cache trong bộ nhớ RAM tiến trình (in-memory).
- Chia sẻ cache, rate-limit và session token qua Redis container (`redis:6379`).
- Refresh token phải được băm SHA-256 và áp dụng cơ chế token rotation.
- Không expose trực tiếp cổng 8000 của backend ra host; toàn bộ request từ client phải đi qua Traefik port 80.

### V. Security & Cyber Defense by Design (NON-NEGOTIABLE)
Mọi thiết kế và dòng code phải tuân thủ nghiêm ngặt các rào chắn an ninh thông tin, phòng chống các lỗ hổng OWASP Top 10 và OWASP Top 10 for LLM:
1. **Kiểm soát truy cập & Chống IDOR (Insecure Direct Object Reference)**:
   - Phân quyền RBAC nghiêm ngặt theo 3 role: `HR`, `Interviewer`, `Council`.
   - Cấm tin cậy client-provided IDs: Mọi API truy xuất session, note, ứng viên phải kiểm tra tính sở hữu (`user_id == current_user.id`) hoặc quyền được phân công cụ thể trong session.
2. **Chống Injection & Rà soát đầu vào**:
   - 100% dữ liệu đầu vào phải được validate qua Pydantic v2 schemas với ràng buộc chặt chẽ về type, regex, độ dài.
   - 100% truy vấn DB qua SQLAlchemy 2.0 ORM / parameterized queries; tuyệt đối cấm nối chuỗi raw SQL.
   - Frontend React escape output mặc định; tuyệt đối cấm dùng `dangerouslySetInnerHTML`.
3. **An toàn File Upload & MinIO (CV / Tài liệu / Audio)**:
   - Kiểm tra định dạng qua Magic Bytes (File Signature), không chỉ dựa vào đuôi mở rộng file (`.pdf`, `.docx`, `.mp3`).
   - Giới hạn cứng kích thước upload tối đa (max payload size) ngăn chặn DoS cạn kiệt tài nguyên.
   - Lưu trữ trên MinIO bằng UUID ngẫu nhiên làm object key; cấm dùng filename gốc của client (chống Path Traversal).
   - MinIO bucket đặt chế độ Private; chỉ truy xuất qua Presigned URL có hạn ngắn hoặc qua API trung gian đã xác thực.
4. **An toàn AI & Chống Prompt Injection (OWASP for LLM)**:
   - Dữ liệu từ ứng viên (CV trích xuất, câu trả lời) là untrusted data; bắt buộc phải phân tách bằng delimiter rõ ràng (XML tags/markdown fences) và sanitize trước khi đưa vào LLM context.
   - Không chuyển thông tin nhạy cảm PII (CCCD/CMND, số thẻ ngân hàng, dữ liệu riêng tư) ra API LLM bên thứ ba.
   - Áp dụng token budget và timeout cho mọi request gọi LLM, ngăn chặn tấn công DoS chi phí/băng thông.
5. **Bảo mật Hạ tầng & Quản lý Bí mật**:
   - Tuyệt đối không hardcode API keys, JWT secret, database credentials trong source code hoặc git.
   - Các dịch vụ backend, postgres, redis, minio chạy trong Docker network nội bộ; chỉ Traefik mở cổng 80/443 ra ngoài.
   - Kích hoạt rate-limiting dựa trên Redis trên các endpoint nhạy cảm (auth, LLM generation, file upload) chống Brute-force và DoS.

### VI. Quality Gates & Test-Driven Discipline (NON-NEGOTIABLE)
Mọi tính năng hoặc thay đổi code bắt buộc phải vượt qua các cổng chất lượng trước khi coi là hoàn tất:
- Backend: Chạy `ruff check` sạch lint và `pytest tests/` pass 100% (bao gồm cả test case bảo mật phân quyền).
- Frontend: Chạy `npm run build` (TypeScript check & Vite build) không có lỗi type.
- Doc Integrity: Bảo toàn docstrings, type annotations và comments giải thích kiến trúc khi refactor.

## Architecture & Technology Constraints
- **Backend**: Python 3.11, FastAPI, Pydantic v2 (schema validation), SQLAlchemy 2.0 (ORM), Alembic (DB migrations), PostgreSQL 16. Chuẩn đặt tên Python: `snake_case`.
- **Frontend**: React (18/19), TypeScript (`strict: true`), Vite. Chuẩn đặt tên TypeScript: `camelCase`. Giao diện phân tách nghiêm ngặt theo 3 vai trò: **HR**, **Interviewer**, **Council**.
- **Storage & Infrastructure**: MinIO (S3-compatible object storage cho CV và tài liệu ứng viên), Redis 7, Docker Compose, Traefik v3.
- **AI & Processing**: Anthropic Claude / Groq API, STT với faster-whisper, pipeline bóc tách CV (pdfplumber, python-docx).

## Development Workflow & Spec Kit Lifecycle
1. **Constitution**: Nền tảng nguyên tắc bất khả xâm phạm (Bảo mật, HITL, Quyền riêng tư, Kiến trúc).
2. **Specification (`speckit-specify`)**: Xác định mục tiêu, phân rã User Stories độc lập (P1, P2,...), kịch bản Given/When/Then, Security & Abuse cases, Success Criteria đo lường được.
3. **Technical Plan (`speckit-plan`)**: Đối chiếu Constitution Check (đặc biệt là Security Gates), phân tích kiến trúc, thiết kế Data Model, Interface Contracts và Quickstart guide.
4. **Tasks Breakdown (`speckit-tasks`)**: Lập danh sách task chi tiết theo thứ tự phụ thuộc, gắn nhãn kiểm thử TDD (bao gồm Security Tests).
5. **Implementation (`speckit-implement`)**: Viết test trước, implement code đáp ứng test, chạy verify qua ruff, pytest, npm build.

## Governance
- Mọi thiết kế hoặc pull request vi phạm các nguyên tắc cốt lõi (đặc biệt là Security & HITL) sẽ bị chặn ngay tại bước Constitution Check trong Technical Plan.
- Mỗi khi phát hiện sai lầm, lỗ hổng hoặc hành vi cần tránh, lập tức cập nhật vào mục "Lessons Learned" trong `AGENTS.md`.

**Version**: 1.1.0 | **Ratified**: 2026-09-17 | **Last Amended**: 2026-09-17
