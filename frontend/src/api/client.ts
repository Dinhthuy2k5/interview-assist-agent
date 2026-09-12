import { ApiError, parseApiErrorMessage } from "../utils/errors";

// Trỏ qua Traefik (port 80, cửa ngõ duy nhất) thay vì thẳng 1 backend instance
// cố định (":8000") - nếu giữ ":8000", frontend luôn gọi đúng 1 container, bỏ
// qua hoàn toàn load balancer, --scale backend=3 sẽ vô nghĩa với frontend.
export const API_BASE_URL = "http://localhost";

const ACCESS_TOKEN_KEY = "iaa_access_token";
const REFRESH_TOKEN_KEY = "iaa_refresh_token";

export function getStoredAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setStoredTokens(accessToken: string | null, refreshToken: string | null): void {
    if (accessToken) {
        localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    } else {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
    }
    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    } else {
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
}

// Đảm bảo nhiều request cùng lúc bị 401 chỉ kích hoạt ĐÚNG 1 lần gọi /auth/refresh
// thật sự - backend dùng cơ chế rotation (refresh_token chỉ dùng được 1 lần),
// nếu 2 request tự ý refresh riêng lẻ, request thứ 2 sẽ dùng refresh_token ĐÃ BỊ
// request thứ 1 revoke -> bị từ chối oan, logout nhầm dù phiên vẫn còn hạn.
let refreshPromise: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!response.ok) return null;

        const data = await response.json();
        setStoredTokens(data.access_token, data.refresh_token);
        return data.access_token as string;
    } catch {
        return null;
    }
}

function refreshAccessToken(): Promise<string | null> {
    if (!refreshPromise) {
        refreshPromise = performRefresh().finally(() => {
            refreshPromise = null;
        });
    }
    return refreshPromise;
}

function buildHeaders(token: string | null, base?: HeadersInit): Headers {
    const headers = new Headers(base);
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const accessToken = getStoredAccessToken();
    let response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: buildHeaders(accessToken, options?.headers),
    });

    if (response.status === 401) {
        // Access token có thể chỉ đơn giản là hết hạn (bình thường, xảy ra mỗi
        // 30 phút) - thử refresh trước khi coi là mất phiên thật sự.
        const newAccessToken = await refreshAccessToken();

        if (newAccessToken) {
            response = await fetch(`${API_BASE_URL}${path}`, {
                ...options,
                headers: buildHeaders(newAccessToken, options?.headers),
            });
        } else {
            // Refresh cũng thất bại - refresh_token đã hết hạn/bị revoke/không
            // còn hợp lệ. Đây mới là lúc thực sự cần đăng nhập lại.
            setStoredTokens(null, null);
            window.location.reload();
            throw new Error("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.");
        }
    }

    if (!response.ok) {
        const body = await response.text();
        const friendlyMsg = parseApiErrorMessage(body, response.status);
        throw new ApiError(response.status, friendlyMsg, body);
    }
    return response.json() as Promise<T>;
}