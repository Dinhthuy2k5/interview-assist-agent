import { useEffect, useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import LoginPage from "./pages/LoginPage";
import JobUploadPage from "./pages/JobUploadPage";
import JobListPage from "./pages/JobListPage";
import FrameworkManagePage from "./pages/FrameworkManagePage";
import UserManagePage from "./pages/UserManagePage";
import SessionManagePage from "./pages/SessionManagePage";
import InterviewerSessionsPage from "./pages/InterviewerSessionsPage";
import { ROLE_LABEL } from "./types/user";

type Tab = "jobs" | "job-list" | "frameworks" | "sessions" | "my-sessions" | "users";

export default function App() {
    const { user, loading, logout } = useAuth();
    const [tab, setTab] = useState<Tab>("jobs");
    const [initialTabSet, setInitialTabSet] = useState(false);

    // Tab mặc định khác nhau theo role - Interviewer không có quyền vào "Vị trí &
    // JD" (backend chặn hr_admin only), để mặc định "jobs" sẽ gặp lỗi 403 ngay khi
    // đăng nhập. Chỉ chạy 1 lần khi user vừa xác định xong (không ghi đè lựa chọn
    // tab thủ công của người dùng sau đó).
    useEffect(() => {
        if (!initialTabSet && user) {
            if (user.role === "interviewer") setTab("my-sessions");
            setInitialTabSet(true);
        }
    }, [user, initialTabSet]);

    if (loading) {
        return <div className="app-shell" />;
    }

    if (!user) {
        return <LoginPage />;
    }

    const isHrAdmin = user.role === "hr_admin";
    const isInterviewer = user.role === "interviewer";
    const isCouncil = user.role === "council";

    return (
        <div className="app-shell">
            <header className="topbar">
                <div>
                    <p className="topbar-title">Interview Assist Agent</p>
                    <p className="topbar-subtitle">Trợ lý hỗ trợ phỏng vấn &amp; đánh giá ứng viên</p>
                </div>

                <nav className="topbar-nav">
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${tab === "jobs" ? "is-active" : ""}`}
                            onClick={() => setTab("jobs")}
                        >
                            Vị trí &amp; JD
                        </button>
                    )}
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
                            className={`nav-link ${tab === "sessions" ? "is-active" : ""}`}
                            onClick={() => setTab("sessions")}
                        >
                            Phiên phỏng vấn
                        </button>
                    )}
                    {isInterviewer && (
                        <button
                            type="button"
                            className={`nav-link ${tab === "my-sessions" ? "is-active" : ""}`}
                            onClick={() => setTab("my-sessions")}
                        >
                            Phiên của tôi
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

            {isHrAdmin && tab === "jobs" && <JobUploadPage />}
            {isHrAdmin && tab === "job-list" && <JobListPage />}
            {isHrAdmin && tab === "frameworks" && <FrameworkManagePage />}
            {isHrAdmin && tab === "sessions" && <SessionManagePage />}
            {isHrAdmin && tab === "users" && <UserManagePage />}
            {isInterviewer && tab === "my-sessions" && <InterviewerSessionsPage />}

            {isCouncil && (
                <div className="page-content">
                    <div className="notice notice-warning">
                        Chưa có tính năng nào cho Hội đồng tuyển dụng ở bản này - phần xem tổng hợp
                        đánh giá đang được phát triển ở sprint sau.
                    </div>
                </div>
            )}
        </div>
    );
}