import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchCurrentUser } from "../api/auth";
import { getStoredToken, setStoredToken } from "../api/client";
import type { User } from "../types/user";

interface AuthContextValue {
    user: User | null;
    loading: boolean;
    login: (token: string, user: User) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = getStoredToken();
        if (!token) {
            setLoading(false);
            return;
        }
        // Còn token từ lần trước (reload trang) - xác thực lại với backend thay vì
        // tin token còn hạn, vì token có thể đã hết hạn hoặc bị thu hồi.
        fetchCurrentUser()
            .then(setUser)
            .catch(() => setStoredToken(null))
            .finally(() => setLoading(false));
    }, []);

    function login(token: string, loggedInUser: User) {
        setStoredToken(token);
        setUser(loggedInUser);
    }

    function logout() {
        setStoredToken(null);
        setUser(null);
    }

    return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth phải được gọi bên trong AuthProvider");
    return ctx;
}