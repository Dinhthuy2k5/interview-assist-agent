import { API_BASE_URL, apiFetch } from "./client";
import type { User } from "../types/user";

export interface LoginResult {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: User;
}

export async function login(email: string, password: string): Promise<LoginResult> {
    const form = new URLSearchParams();
    form.set("username", email); // OAuth2PasswordRequestForm ở backend dùng field "username"
    form.set("password", password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
    });

    if (!response.ok) {
        const body = await response.text();
        throw new Error(`API error ${response.status}: ${body}`);
    }
    return response.json();
}

/** Gọi khi user chủ động bấm "Đăng xuất" - revoke refresh_token ở backend, đây
 * mới là bước khiến đăng xuất CÓ HIỆU LỰC THẬT (khác JWT thuần trước đây, chỉ
 * xoá token phía client mà server không hề biết/không thể thu hồi). Không throw
 * lỗi nếu request thất bại - dù sao phía client cũng sẽ xoá token ngay sau đó,
 * không cần chặn UX chỉ vì request logout bị mất mạng. */
export async function logout(refreshToken: string): Promise<void> {
    try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });
    } catch {
        // best-effort - xem comment trên
    }
}

export function fetchCurrentUser(): Promise<User> {
    return apiFetch<User>("/auth/me");
}