/**
 * Custom Error đại diện cho lỗi từ backend API.
 * Giữ nguyên status code HTTP và raw body để phục vụ debugging/logging.
 */
export class ApiError extends Error {
    readonly status: number;
    readonly rawBody: string;

    constructor(status: number, message: string, rawBody: string = "") {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.rawBody = rawBody;
        Object.setPrototypeOf(this, ApiError.prototype);
    }
}

/**
 * Trích xuất message thân thiện cho người dùng từ response body của backend (FastAPI).
 * - FastAPI HTTPException: {"detail": "Nội dung lỗi"}
 * - FastAPI RequestValidationError (422): {"detail": [{"loc": [...], "msg": "..."}]}
 * - Fallback thông điệp tiếng Việt dễ hiểu theo HTTP Status code khi body rỗng hoặc HTML lỗi.
 */
export function parseApiErrorMessage(rawBody: string, status: number): string {
    const trimmed = rawBody ? rawBody.trim() : "";

    if (!trimmed) {
        return getStatusFallbackMessage(status);
    }

    try {
        const parsed = JSON.parse(trimmed);

        if (parsed && typeof parsed === "object") {
            const detail = parsed.detail;

            // Trường hợp 1: detail là chuỗi đơn giản
            if (typeof detail === "string" && detail.trim().length > 0) {
                return detail.trim();
            }

            // Trường hợp 2: detail là mảng validation error của Pydantic/FastAPI
            if (Array.isArray(detail) && detail.length > 0) {
                const messages = detail.map((item) => {
                    if (typeof item === "string") return item;
                    if (item && typeof item === "object") {
                        const loc = Array.isArray(item.loc)
                            ? item.loc.filter((l: unknown) => l !== "body" && l !== "query").join(".")
                            : "";
                        const msg = item.msg || "Dữ liệu không hợp lệ";
                        return loc ? `${loc}: ${msg}` : msg;
                    }
                    return "Dữ liệu không hợp lệ";
                });
                return messages.join("; ");
            }

            // Trường hợp 3: message field thay vì detail
            if (typeof parsed.message === "string" && parsed.message.trim().length > 0) {
                return parsed.message.trim();
            }
        }
    } catch {
        // Không phải JSON (ví dụ HTML 502/504 từ Traefik Gateway hoặc plain text)
    }

    // Nếu là HTML từ proxy (Traefik / Nginx)
    if (trimmed.startsWith("<") || trimmed.includes("<html")) {
        return `Máy chủ phản hồi lỗi ${status} (Gateway/Proxy error). Vui lòng kiểm tra lại kết nối.`;
    }

    // Nếu là chuỗi ngắn có nghĩa
    if (trimmed.length < 120 && !trimmed.includes("\n")) {
        return trimmed;
    }

    return getStatusFallbackMessage(status);
}

function getStatusFallbackMessage(status: number): string {
    switch (status) {
        case 400:
            return "Yêu cầu không hợp lệ. Vui lòng kiểm tra lại thông tin.";
        case 401:
            return "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
        case 403:
            return "Bạn không có quyền thực hiện hành động này.";
        case 404:
            return "Không tìm thấy dữ liệu yêu cầu.";
        case 409:
            return "Dữ liệu bị xung đột hoặc đã tồn tại trên hệ thống.";
        case 422:
            return "Dữ liệu nhập vào chưa đúng định dạng quy định.";
        case 500:
            return "Lỗi máy chủ nội bộ. Vui lòng thử lại sau.";
        case 502:
        case 503:
        case 504:
            return "Dịch vụ máy chủ tạm thời không phản hồi. Vui lòng kiểm tra lại kết nối mạng hoặc container.";
        default:
            return `Yêu cầu thất bại với mã trạng thái ${status}.`;
    }
}
