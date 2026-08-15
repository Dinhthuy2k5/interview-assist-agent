import { useState } from "react";
import { login as loginRequest } from "../api/auth";
import { useAuth } from "../contexts/AuthContext";

export default function LoginPage() {
    const { login } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            const result = await loginRequest(email, password);
            login(result.access_token, result.user);
        } catch {
            setError("Email hoặc mật khẩu không đúng.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="login-shell">
            <div className="card login-card">
                <p className="topbar-title" style={{ margin: 0 }}>
                    Interview Assist Agent
                </p>
                <p className="field-hint" style={{ marginBottom: "1.5rem" }}>
                    Đăng nhập để tiếp tục
                </p>

                <form onSubmit={handleSubmit}>
                    <div className="field">
                        <label htmlFor="login-email">Email</label>
                        <input
                            id="login-email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            autoFocus
                        />
                    </div>
                    <div className="field">
                        <label htmlFor="login-password">Mật khẩu</label>
                        <input
                            id="login-password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button className="btn" type="submit" disabled={submitting} style={{ width: "100%" }}>
                        {submitting ? "Đang đăng nhập..." : "Đăng nhập"}
                    </button>
                    {error && (
                        <div className="notice notice-error" style={{ marginTop: "1rem", marginBottom: 0 }}>
                            {error}
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
}