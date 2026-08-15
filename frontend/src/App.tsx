import { useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import LoginPage from "./pages/LoginPage";
import JobUploadPage from "./pages/JobUploadPage";
import JobListPage from "./pages/JobListPage";
import FrameworkManagePage from "./pages/FrameworkManagePage";
import UserManagePage from "./pages/UserManagePage";
import { ROLE_LABEL } from "./types/user";

type Tab = "jobs" | "job-list" | "frameworks" | "users";

export default function App() {
    const { user, loading, logout } = useAuth();
    const [tab, setTab] = useState<Tab>("jobs");

    if (loading) {
        return <div className="app-shell" />;
    }

    if (!user) {
        return <LoginPage />;
    }

    const isHrAdmin = user.role === "hr_admin";

    return (
        <div className="app-shell">
            <header className="topbar">
                <div>
                    <p className="topbar-title">Interview Assist Agent</p>
                    <p className="topbar-subtitle">Trợ lý hỗ trợ phỏng vấn &amp; đánh giá ứng viên</p>
                </div>

                <nav className="topbar-nav">
                    <button
                        type="button"
                        className={`nav-link ${tab === "jobs" ? "is-active" : ""}`}
                        onClick={() => setTab("jobs")}
                    >
                        Vị trí &amp; JD
                    </button>
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${tab === "job-list" ? "is-active" : ""}`}
                            onClick={() => setTab("job-list")}
                        >
                            Danh sách job
                        </button>
                    )}
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${tab === "frameworks" ? "is-active" : ""}`}
                            onClick={() => setTab("frameworks")}
                        >
                            Khung năng lực
                        </button>
                    )}
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${tab === "users" ? "is-active" : ""}`}
                            onClick={() => setTab("users")}
                        >
                            Người dùng
                        </button>
                    )}
                </nav>

                <div className="topbar-user">
                    <span className="field-hint" style={{ marginTop: 0 }}>
                        {user.full_name} · {ROLE_LABEL[user.role]}
                    </span>
                    <button type="button" className="btn btn-secondary" onClick={logout}>
                        Đăng xuất
                    </button>
                </div>
            </header>

            {tab === "jobs" && <JobUploadPage />}
            {tab === "job-list" && isHrAdmin && <JobListPage />}
            {tab === "frameworks" && isHrAdmin && <FrameworkManagePage />}
            {tab === "users" && isHrAdmin && <UserManagePage />}
        </div>
    );
}