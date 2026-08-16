import { useEffect, useState } from "react";
import { listMySessions } from "../api/sessions";
import type { Session } from "../types/session";
import InterviewSessionCardView from "../components/InterviewSessionCardView";

const STATUS_LABEL: Record<string, string> = {
    scheduled: "Chưa bắt đầu",
    in_progress: "Đang phỏng vấn",
    completed: "Đã hoàn tất",
};

function statusBadgeClass(status: string): string {
    if (status === "completed") return "parsed";
    if (status === "in_progress") return "needs_review";
    return "pending";
}

function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString("vi-VN", { dateStyle: "medium", timeStyle: "short" });
}

export default function InterviewerSessionsPage() {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

    function load() {
        setLoading(true);
        setLoadError(null);
        listMySessions()
            .then(setSessions)
            .catch(() => setLoadError("Không tải được danh sách phiên phỏng vấn."))
            .finally(() => setLoading(false));
    }

    useEffect(load, []);

    if (activeSessionId) {
        return (
            <InterviewSessionCardView
                sessionId={activeSessionId}
                onBack={() => {
                    setActiveSessionId(null);
                    load();
                }}
            />
        );
    }

    return (
        <div className="page-content">
            <h1 className="page-heading">Phiên phỏng vấn của tôi</h1>
            <p className="page-description">
                Các buổi phỏng vấn bạn được phân công. Chọn 1 buổi để ghi note và chấm điểm.
            </p>

            {loadError && <div className="notice notice-error">{loadError}</div>}
            {loading ? (
                <p className="field-hint">Đang tải...</p>
            ) : sessions.length === 0 ? (
                <div className="notice notice-warning">Bạn chưa được phân công phiên phỏng vấn nào.</div>
            ) : (
                <div className="question-list">
                    {sessions.map((s) => (
                        <div key={s.id} className="question-card">
                            <div className="question-card-header">
                                <div>
                                    <p className="question-criterion">{s.candidate_name}</p>
                                    <p className="question-weight">{formatDateTime(s.scheduled_at)}</p>
                                </div>
                                <span className={`status-badge ${statusBadgeClass(s.status)}`}>
                                    {STATUS_LABEL[s.status]}
                                </span>
                            </div>
                            {s.candidate_info && <p className="question-rationale">{s.candidate_info}</p>}
                            <div className="question-actions">
                                <button type="button" className="btn" onClick={() => setActiveSessionId(s.id)}>
                                    {s.status === "completed" ? "Xem lại" : "Vào phỏng vấn"}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}