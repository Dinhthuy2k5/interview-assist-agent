import { useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import LoginPage from "./pages/LoginPage";
import JobUploadPage from "./pages/JobUploadPage";
import JobListPage from "./pages/JobListPage";
import FrameworkManagePage from "./pages/FrameworkManagePage";
import UserManagePage from "./pages/UserManagePage";
import SessionManagePage from "./pages/SessionManagePage";
import InterviewerSessionsPage from "./pages/InterviewerSessionsPage";
import CouncilReportPage from "./pages/CouncilReportPage";
import { ROLE_LABEL, type UserRole } from "./types/user";

type Tab = "jobs" | "job-list" | "frameworks" | "sessions" | "my-sessions" | "reports" | "users";

function defaultTabForRole(role: UserRole): Tab {
    if (role === "interviewer") return "my-sessions";
    if (role === "council") return "reports";
    return "jobs";
}

export default function App() {
    const { user, loading, logout } = useAuth();
    // null = người dùng CHƯA tự bấm tab nào - dùng effectiveTab (tính theo role)
    // làm mặc định. Không dùng useEffect để set tab mặc định sau khi user xuất
    // hiện - cách đó cần thêm 1 vòng render nữa mới đúng, và có trường hợp vòng
    // render đó không xảy ra kịp (trang trắng, không request nào được gọi, phải
    // F5 mới đúng). Tính effectiveTab NGAY trong lần render đầu tiên khi user có
    // sẵn - không phụ thuộc vòng render thứ 2 nào cả.
    const [tab, setTab] = useState<Tab | null>(null);

    if (loading) {
        return <div className="app-shell" />;
    }

    if (!user) {
        return <LoginPage />;
    }

    const isHrAdmin = user.role === "hr_admin";
    const isInterviewer = user.role === "interviewer";
    const isCouncil = user.role === "council";
    const effectiveTab: Tab = tab ?? defaultTabForRole(user.role);

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
                            className={`nav-link ${effectiveTab === "jobs" ? "is-active" : ""}`}
                            onClick={() => setTab("jobs")}
                        >
                            Vị trí &amp; JD
                        </button>
                    )}
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${effectiveTab === "job-list" ? "is-active" : ""}`}
                            onClick={() => setTab("job-list")}
                        >
                            Danh sách job
                        </button>
                    )}
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${effectiveTab === "frameworks" ? "is-active" : ""}`}
                            onClick={() => setTab("frameworks")}
                        >
                            Khung năng lực
                        </button>
                    )}
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${effectiveTab === "sessions" ? "is-active" : ""}`}
                            onClick={() => setTab("sessions")}
                        >
                            Phiên phỏng vấn
                        </button>
                    )}
                    {isInterviewer && (
                        <button
                            type="button"
                            className={`nav-link ${effectiveTab === "my-sessions" ? "is-active" : ""}`}
                            onClick={() => setTab("my-sessions")}
                        >
                            Phiên của tôi
                        </button>
                    )}
                    {isCouncil && (
                        <button
                            type="button"
                            className={`nav-link ${effectiveTab === "reports" ? "is-active" : ""}`}
                            onClick={() => setTab("reports")}
                        >
                            Báo cáo đánh giá
                        </button>
                    )}
                    {isHrAdmin && (
                        <button
                            type="button"
                            className={`nav-link ${effectiveTab === "users" ? "is-active" : ""}`}
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

            {isHrAdmin && effectiveTab === "jobs" && <JobUploadPage />}
            {isHrAdmin && effectiveTab === "job-list" && <JobListPage />}
            {isHrAdmin && effectiveTab === "frameworks" && <FrameworkManagePage />}
            {isHrAdmin && effectiveTab === "sessions" && <SessionManagePage />}
            {isHrAdmin && effectiveTab === "users" && <UserManagePage />}
            {isInterviewer && effectiveTab === "my-sessions" && <InterviewerSessionsPage />}
            {isCouncil && effectiveTab === "reports" && <CouncilReportPage />}
        </div>
    );
}