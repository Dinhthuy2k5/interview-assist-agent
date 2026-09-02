import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchCurrentUser, logout as logoutRequest } from "../api/auth";
import { getStoredAccessToken, getStoredRefreshToken, setStoredTokens } from "../api/client";
import type { User } from "../types/user";

interface AuthContextValue {
    user: User | null;
    loading: boolean;
    login: (accessToken: string, refreshToken: string, user: User) => void;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = getStoredAccessToken();
        if (!token) {
            setLoading(false);
            return;
        }
        // Còn access_token từ lần trước (reload trang) - xác thực lại với backend
        // thay vì tin token còn hạn. Nếu access_token đã hết hạn, apiFetch (trong
        // fetchCurrentUser) TỰ ĐỘNG thử refresh bằng refresh_token trước khi thất
        // bại hẳn - không cần tự xử lý refresh riêng ở đây.
        fetchCurrentUser()
            .then(setUser)
            .catch(() => setStoredTokens(null, null))
            .finally(() => setLoading(false));
    }, []);

    function login(accessToken: string, refreshToken: string, loggedInUser: User) {
        setStoredTokens(accessToken, refreshToken);
        setUser(loggedInUser);
    }

    async function logout() {
        // Revoke refresh_token ở backend TRƯỚC - đây là bước khiến đăng xuất có
        // hiệu lực thật (khác JWT thuần trước đây). best-effort: dù request lỗi
        // (mất mạng...), vẫn xoá token phía client ngay sau đó, không chặn UX.
        const refreshToken = getStoredRefreshToken();
        if (refreshToken) {
            await logoutRequest(refreshToken);
        }
        setStoredTokens(null, null);
        setUser(null);
    }

    return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth phải được gọi bên trong AuthProvider");
    return ctx;
}