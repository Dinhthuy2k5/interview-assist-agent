import { useEffect, useState } from "react";
import { createUser, listUsers } from "../api/users";
import { ROLE_LABEL, type User, type UserRole } from "../types/user";

const ROLES: UserRole[] = ["hr_admin", "interviewer", "council"];

export default function UserManagePage() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    const [email, setEmail] = useState("");
    const [fullName, setFullName] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState<UserRole>("interviewer");
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);

    function loadUsers() {
        setLoading(true);
        setLoadError(null);
        listUsers()
            .then(setUsers)
            .catch(() => setLoadError("Không tải được danh sách người dùng."))
            .finally(() => setLoading(false));
    }

    useEffect(loadUsers, []);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setSubmitting(true);
        setSubmitError(null);
        try {
            await createUser({ email, full_name: fullName, password, role });
            setEmail("");
            setFullName("");
            setPassword("");
            setRole("interviewer");
            loadUsers();
        } catch (e) {
            setSubmitError(e instanceof Error ? e.message : "Tạo tài khoản thất bại.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="page-content">
            <h1 className="page-heading">Quản lý người dùng</h1>
            <p className="page-description">
                Tạo tài khoản cho Interviewer và Hội đồng tuyển dụng. Người dùng tự đổi mật khẩu
                sau lần đăng nhập đầu (Sprint sau) — hiện tại gửi mật khẩu tạm qua kênh riêng, không
                qua email công khai.
            </p>

            <div className="card">
                <h3 style={{ marginTop: 0, fontSize: "1rem" }}>Tạo tài khoản mới</h3>
                <form onSubmit={handleSubmit}>
                    <div className="field">
                        <label htmlFor="user-email">Email</label>
                        <input
                            id="user-email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className="field">
                        <label htmlFor="user-name">Họ tên</label>
                        <input
                            id="user-name"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            required
                        />
                    </div>
                    <div className="field">
                        <label htmlFor="user-password">Mật khẩu tạm thời</label>
                        <input
                            id="user-password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            minLength={8}
                            required
                        />
                        <p className="field-hint">Tối thiểu 8 ký tự.</p>
                    </div>
                    <div className="field">
                        <label htmlFor="user-role">Vai trò</label>
                        <select id="user-role" value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
                            {ROLES.map((r) => (
                                <option key={r} value={r}>
                                    {ROLE_LABEL[r]}
                                </option>
                            ))}
                        </select>
                    </div>
                    <button className="btn" type="submit" disabled={submitting}>
                        {submitting ? "Đang tạo..." : "Tạo tài khoản"}
                    </button>
                    {submitError && (
                        <div className="notice notice-error" style={{ marginTop: "1rem", marginBottom: 0 }}>
                            {submitError}
                        </div>
                    )}
                </form>
            </div>

            <h2 className="page-heading" style={{ fontSize: "1.15rem", marginTop: "2rem" }}>
                Danh sách người dùng
            </h2>
            {loadError && <div className="notice notice-error">{loadError}</div>}
            {loading ? (
                <p className="field-hint">Đang tải...</p>
            ) : users.length === 0 ? (
                <div className="notice notice-warning">Chưa có người dùng nào.</div>
            ) : (
                <div className="card">
                    <table className="user-table">
                        <thead>
                            <tr>
                                <th>Họ tên</th>
                                <th>Email</th>
                                <th>Vai trò</th>
                                <th>Trạng thái</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((u) => (
                                <tr key={u.id}>
                                    <td>{u.full_name}</td>
                                    <td>{u.email}</td>
                                    <td>{ROLE_LABEL[u.role]}</td>
                                    <td>
                                        <span className={`status-badge ${u.is_active ? "parsed" : "pending"}`}>
                                            {u.is_active ? "Đang hoạt động" : "Đã khoá"}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}