import { useEffect, useState } from "react";
import { listSessions } from "../api/sessions";
import { listJobs } from "../api/jobs";
import type { Job } from "../types/job";
import type { Session } from "../types/session";
import AggregationPanel from "../components/AggregationPanel";
import SessionQuestionsPanel from "../components/SessionQuestionsPanel";
import DecisionPanel from "../components/DecisionPanel";

const STATUS_LABEL: Record<string, string> = {
    scheduled: "Chưa bắt đầu",
    in_progress: "Đang phỏng vấn",
    completed: "Đã hoàn tất",
};

type DetailTab = "aggregation" | "questions" | "decision";

function statusBadgeClass(status: string): string {
    if (status === "completed") return "parsed";
    if (status === "in_progress") return "needs_review";
    return "pending";
}

function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString("vi-VN", { dateStyle: "medium", timeStyle: "short" });
}

export default function CouncilReportPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [detailTab, setDetailTab] = useState<DetailTab>("aggregation");

    function load() {
        setLoading(true);
        setLoadError(null);
        Promise.all([listJobs("all"), listSessions()])
            .then(([jobsData, sessionsData]) => {
                setJobs(jobsData);
                setSessions(sessionsData);
            })
            .catch(() => setLoadError("Không tải được dữ liệu."))
            .finally(() => setLoading(false));
    }

    useEffect(load, []);

    function jobTitle(id: string): string {
        return jobs.find((j) => j.id === id)?.title ?? "(job không xác định)";
    }

    function selectSession(id: string) {
        setSelectedSessionId(id);
        setDetailTab("aggregation");
    }

    return (
        <div className="page-content">
            <h1 className="page-heading">Báo cáo đánh giá</h1>
            <p className="page-description">
                Xem tổng hợp đánh giá, câu hỏi đã hỏi, và ghi quyết định cuối cho từng buổi phỏng vấn.
                Báo cáo tổng hợp là dữ liệu tư vấn (advisory) - quyết định vẫn do Hội đồng tự cân nhắc.
            </p>

            {loadError && <div className="notice notice-error">{loadError}</div>}
            {loading ? (
                <p className="field-hint">Đang tải...</p>
            ) : sessions.length === 0 ? (
                <div className="notice notice-warning">Chưa có phiên phỏng vấn nào.</div>
            ) : (
                <div className="session-workspace">
                    <div className="session-list-col">
                        {sessions.map((s) => (
                            <button
                                key={s.id}
                                type="button"
                                className={`session-list-item ${selectedSessionId === s.id ? "is-selected" : ""}`}
                                onClick={() => selectSession(s.id)}
                            >
                                <span className="session-list-name">{s.candidate_name}</span>
                                <span className="session-list-meta">
                                    {jobTitle(s.job_id)} · {formatDateTime(s.scheduled_at)}
                                </span>
                                <span className={`status-badge ${statusBadgeClass(s.status)}`}>
                                    {STATUS_LABEL[s.status]}
                                </span>
                            </button>
                        ))}
                    </div>

                    <div className="session-detail-col">
                        {selectedSessionId ? (
                            <>
                                <div className="detail-tabs">
                                    {(
                                        [
                                            { key: "aggregation", label: "Báo cáo tổng hợp" },
                                            { key: "questions", label: "Câu hỏi đã hỏi" },
                                            { key: "decision", label: "Quyết định" },
                                        ] as { key: DetailTab; label: string }[]
                                    ).map((t) => (
                                        <button
                                            key={t.key}
                                            type="button"
                                            className={`detail-tab ${detailTab === t.key ? "is-active" : ""}`}
                                            onClick={() => setDetailTab(t.key)}
                                        >
                                            {t.label}
                                        </button>
                                    ))}
                                </div>

                                {detailTab === "aggregation" && (
                                    <AggregationPanel sessionId={selectedSessionId} canTrigger={false} />
                                )}
                                {detailTab === "questions" && (
                                    <SessionQuestionsPanel sessionId={selectedSessionId} />
                                )}
                                {detailTab === "decision" && (
                                    <DecisionPanel sessionId={selectedSessionId} canSubmit />
                                )}
                            </>
                        ) : (
                            <div className="detail-placeholder">
                                Chọn 1 phiên phỏng vấn bên trái để xem báo cáo, câu hỏi và ghi quyết định.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}