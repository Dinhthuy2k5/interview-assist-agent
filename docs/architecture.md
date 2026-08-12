# Kiến trúc hệ thống

## Tổng quan

Interview Assist Agent gồm 5 service tách biệt, giao tiếp qua REST API, dùng chung
1 PostgreSQL và 1 MinIO. Nguyên tắc thiết kế cốt lõi: **Aggregation Service không có
quyền ghi vào bảng `Decision`** — chỉ Decision Service (thao tác qua UI bởi hội đồng)
mới ghi được. Đây là cách enforce HITL (Human-In-The-Loop) ở tầng kiến trúc, không
chỉ ở tầng convention hay tài liệu.

\`\`\`mermaid
flowchart TB
    subgraph FE["Frontend (Web App)"]
        HR[HR Dashboard]
        IC[Interviewer Console]
        CR[Council Review Dashboard]
    end

    GW["API Gateway / BFF<br/>(auth, rate limit, routing)"]

    subgraph Services["Backend Services"]
        JDP["JD Parse Service"]
        QG["Question Gen Service<br/>(Agent)"]
        SN["Session & Note Service"]
        AG["Aggregation Service<br/>(Agent)"]
        DEC["Decision Service<br/>(Human-only writes)"]
    end

    DB[("PostgreSQL")]
    OBJ[("MinIO<br/>(JD files, audio)")]

    HR --> GW
    IC --> GW
    CR --> GW

    GW --> JDP
    GW --> QG
    GW --> SN
    GW --> AG
    GW --> DEC

    JDP --> DB
    JDP --> OBJ
    QG --> DB
    SN --> DB
    SN --> OBJ
    AG --> DB
    DEC --> DB

    AG -.->|"advisory only<br/>KHÔNG được ghi Decision"| DEC

    style DEC fill:#2d5016,color:#fff
    style AG fill:#5c1a1a,color:#fff
\`\`\`

## Luồng dữ liệu chính (happy path)

\`\`\`mermaid
sequenceDiagram
    participant HR as HR Admin
    participant JDP as JD Parse
    participant QG as Question Gen Agent
    participant IV as Interviewer
    participant SN as Session & Note
    participant AG as Aggregation Agent
    participant Council as Hội đồng
    participant DEC as Decision Service

    HR->>JDP: Upload JD (PDF/docx)
    JDP-->>HR: jd_text đã parse (hoặc needs_review)
    HR->>QG: Yêu cầu sinh câu hỏi
    QG-->>HR: Câu hỏi + rationale (đã qua Sensitive-Attribute Filter)
    HR->>HR: Duyệt / sửa câu hỏi

    IV->>SN: Ghi note + điểm theo từng criterion (trong buổi phỏng vấn)
    IV->>SN: Upload audio (batch STT sau buổi)
    SN-->>IV: Transcript + gợi ý note (không tự chấm điểm)

    Note over AG: Nhiều interviewer cùng 1 session
    AG->>SN: Đọc toàn bộ note/điểm
    AG->>AG: Rule-based variance check + embedding similarity check
    AG->>AG: Nếu conflict -> LLM semantic check
    AG-->>Council: Aggregation Report (kèm rationale_trace)

    Council->>DEC: Xem report + note gốc, ra quyết định cuối
    DEC->>DEC: Ghi final_decision (chỉ role hội đồng mới gọi được)
\`\`\`

## Vì sao tách Aggregation Report và Decision thành 2 bảng riêng

`Aggregation Report` là **output của AI** — mang tính advisory, có thể sai, phải
luôn kèm `rationale_trace` để giải thích được. `Decision` là **action của người** —
authoritative, không thể bị agent nào ghi đè hay tự động hoá. Tách bảng + tách
service là cách hiện thực hoá ràng buộc HITL bắt buộc ở tầng data model, thay vì
chỉ dựa vào quy ước "đừng tự động hoá" dễ bị vi phạm khi code phát triển thêm.

## Tech stack

| Layer | Công nghệ |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Frontend | React + TypeScript (Vite) |
| Database | PostgreSQL 16 |
| Object Storage | MinIO (S3-compatible, self-host) |
| STT | Whisper self-host (faster-whisper), batch xử lý |
| LLM | Claude API — Question Gen, Aggregation semantic check |
| Embedding | sentence-transformers (self-host) — pre-check trước khi gọi LLM |
| Auth | JWT + RBAC middleware |
| Containerize | Docker + docker-compose |

## Liên quan

- [Data Model](data-model.md)
- [ADR 0001: Microservice boundaries & HITL enforcement](decisions/0001-microservice-boundaries-and-hitl-enforcement.md)