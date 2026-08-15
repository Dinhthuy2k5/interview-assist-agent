export const API_BASE_URL = "http://localhost:8000";

const TOKEN_STORAGE_KEY = "iaa_access_token";

export function getStoredToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
    if (token) {
        localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const token = getStoredToken();
    const headers = new Headers(options?.headers);
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

    if (response.status === 401) {
        // Token hết hạn/không hợp lệ - xoá và reload để AuthProvider phát hiện
        // mất token, tự động quay lại màn hình đăng nhập. Đơn giản nhưng chắc
        // chắn hơn cố gắng điều hướng in-app từ 1 file không phải React component.
        setStoredToken(null);
        window.location.reload();
    }

    if (!response.ok) {
        const body = await response.text();
        throw new Error(`API error ${response.status}: ${body}`);
    }
    return response.json() as Promise<T>;
}