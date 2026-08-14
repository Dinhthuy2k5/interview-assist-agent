import { useState } from "react";
import JobUploadPage from "./pages/JobUploadPage";
import FrameworkManagePage from "./pages/FrameworkManagePage";

type Tab = "jobs" | "frameworks";

export default function App() {
    const [tab, setTab] = useState<Tab>("jobs");

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
                    <button
                        type="button"
                        className={`nav-link ${tab === "frameworks" ? "is-active" : ""}`}
                        onClick={() => setTab("frameworks")}
                    >
                        Khung năng lực
                    </button>
                </nav>

                <span className="auth-badge">Đăng nhập &amp; phân quyền: chưa cấu hình (Sprint 6)</span>
            </header>

            {tab === "jobs" ? <JobUploadPage /> : <FrameworkManagePage />}
        </div>
    );
}