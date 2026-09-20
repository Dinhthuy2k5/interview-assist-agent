import { useState } from "react";
import { login as loginRequest } from "../api/auth";
import { useAuth } from "../contexts/AuthContext";

export default function LoginPage() {
    const { login } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function performLogin(targetEmail: string, targetPass: string) {
        setSubmitting(true);
        setError(null);
        try {
            const result = await loginRequest(targetEmail, targetPass);
            login(result.access_token, result.refresh_token, result.user);
        } catch {
            setError("Email hoặc mật khẩu không đúng.");
        } finally {
            setSubmitting(false);
        }
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        await performLogin(email, password);
    }

    async function handleDemoLogin() {
        const demoEmail = "hradmin@gmail.com";
        const demoPass = "hradmin@";
        setEmail(demoEmail);
        setPassword(demoPass);
        await performLogin(demoEmail, demoPass);
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

                    <div
                        style={{
                            margin: "1.25rem 0 1rem",
                            display: "flex",
                            alignItems: "center",
                            gap: "0.75rem",
                            color: "var(--color-ink-muted)",
                            fontSize: "0.8rem",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                        }}
                    >
                        <hr style={{ flex: 1, border: "none", borderTop: "1px solid var(--color-border)" }} />
                        <span>HOẶC</span>
                        <hr style={{ flex: 1, border: "none", borderTop: "1px solid var(--color-border)" }} />
                    </div>

                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={handleDemoLogin}
                        disabled={submitting}
                        style={{
                            width: "100%",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "0.5rem",
                        }}
                    >
                        <span>🚀</span>
                        <span>Đăng nhập tài khoản mẫu (Demo HR)</span>
                    </button>
                    <p
                        className="field-hint"
                        style={{
                            textAlign: "center",
                            marginTop: "0.5rem",
                            marginBottom: 0,
                            fontSize: "0.8rem",
                        }}
                    >
                        Trải nghiệm đầy đủ tính năng dành cho khách truy cập.
                    </p>

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