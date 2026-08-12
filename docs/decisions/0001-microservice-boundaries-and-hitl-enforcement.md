# ADR 0001: Tách Aggregation Service và Decision Service để enforce HITL ở tầng kiến trúc

**Trạng thái:** Chấp nhận
**Ngày:** 2026-08-12
**Bối cảnh Sprint:** Sprint 0 (thiết kế nền tảng)

## Bối cảnh

Đề bài (BO-17) yêu cầu HITL (Human-In-The-Loop) **bắt buộc**: agent chỉ được đưa
khuyến nghị, quyết định tuyển dụng cuối cùng phải do con người (hội đồng) thực hiện.

Cách hiện thực HITL phổ biến nhưng yếu là chỉ dựa vào **quy ước ở tầng ứng dụng**
(VD: "endpoint tổng hợp không tự động gửi email kết quả") — cách này dễ vỡ khi:
- Code phát triển thêm, dev sau này (hoặc chính mình sau vài tháng) vô tình thêm
  logic tự động hoá vào Aggregation Service mà không nhận ra đang vi phạm HITL
- Không có cách nào chứng minh được (audit) rằng HITL luôn được tuân thủ, chỉ có
  thể tin vào review code thủ công

## Quyết định

Tách hoàn toàn **Aggregation Service** và **Decision Service** thành 2 service độc
lập, với ràng buộc ở tầng kiến trúc:

1. Aggregation Service chỉ có quyền **đọc** dữ liệu note/score và **ghi** vào bảng
   `aggregation_report` (advisory, không phải kết quả cuối)
2. Aggregation Service **không có credential/quyền ghi** vào bảng `decision` —
   không phải "không được phép theo quy ước", mà là **không thể về mặt kỹ thuật**
   (khác connection string / role DB, hoặc tách hẳn service account nếu sau này
   có message queue giữa 2 service)
3. Chỉ Decision Service — được gọi từ UI của hội đồng, có xác thực role cụ thể —
   mới ghi được bảng `decision`
4. Mọi bản ghi trong `aggregation_report` bắt buộc có `rationale_trace` — không cho
   phép chỉ trả về 1 con số/khuyến nghị trần trụi không giải thích được

## Vì sao chọn cách này thay vì các lựa chọn khác

| Lựa chọn | Vì sao không chọn |
|---|---|
| 1 service duy nhất xử lý cả tổng hợp lẫn quyết định, có flag `auto_decide=false` | Flag là quy ước ở tầng code, dễ bị đổi nhầm hoặc bypass khi thêm tính năng sau này; không có ranh giới kỹ thuật thật sự |
| Chỉ enforce ở tầng UI (không hiện nút "tự động duyệt") | Backend vẫn có khả năng kỹ thuật để tự động hoá nếu ai đó gọi thẳng API — UI không phải là security boundary |
| Tách service nhưng dùng chung DB credential | Nếu Aggregation Service bị lỗi logic hoặc bị compromise, vẫn có thể ghi nhầm/ghi ác ý vào `decision` |

## Đánh đổi (Trade-offs) — chấp nhận cho scope hiện tại

- Với quy mô self-host 1 người dùng thử (MVP hiện tại), tách DB credential/role
  riêng cho từng service là hơi over-engineering so với lợi ích ngay lập tức —
  **nhưng vẫn chọn làm** vì đây là điểm cốt lõi thể hiện đúng constraint "HITL bắt
  buộc" của đề bài, và tập thói quen đúng ngay từ đầu rẻ hơn nhiều so với refactor
  lại sau khi hệ thống đã lớn
- Việc gọi giữa các service qua REST API (thay vì gọi hàm trực tiếp trong cùng 1
  process) tăng độ phức tạp vận hành (network call, retry, timeout) — chấp nhận
  đánh đổi này vì lợi ích tách boundary rõ ràng lớn hơn

## Hệ quả

- Data model: `aggregation_report` và `decision` là 2 bảng tách biệt hoàn toàn
  (xem [data-model.md](../data-model.md)), không có bảng nào gộp chung 2 khái niệm
- Sprint 6 (Decision Service + RBAC) phải implement kiểm tra role nghiêm ngặt:
  chỉ user có role "hội đồng" mới gọi được endpoint ghi `decision`
- Khi viết test cho Aggregation Service, cần có test case xác nhận **không tồn
  tại** đường dẫn code nào từ Aggregation Service ghi thẳng vào bảng `decision`