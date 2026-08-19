import { Fragment, useEffect, useState } from "react";
import { listSessions } from "../api/sessions";
import { listJobs } from "../api/jobs";
import type { Job } from "../types/job";
import type { Session } from "../types/session";
import AggregationPanel from "../components/AggregationPanel";

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

export default function CouncilReportPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);

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

    return (
        <div className="page-content">
            <h1 className="page-heading">Báo cáo đánh giá</h1>
            <p className="page-description">
                Xem tổng hợp đánh giá từ các interviewer cho từng buổi phỏng vấn. Đây là dữ liệu tư
                vấn (advisory) - quyết định cuối cùng vẫn do Hội đồng tự cân nhắc dựa trên toàn bộ
                thông tin, không phải do hệ thống tự động quyết định.
            </p>

            {loadError && <div className="notice notice-error">{loadError}</div>}
            {loading ? (
                <p className="field-hint">Đang tải...</p>
            ) : sessions.length === 0 ? (
                <div className="notice notice-warning">Chưa có phiên phỏng vấn nào.</div>
            ) : (
                <div className="card">
                    <table className="user-table">
                        <thead>
                            <tr>
                                <th>Ứng viên</th>
                                <th>Job</th>
                                <th>Thời gian</th>
                                <th>Trạng thái</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {sessions.map((s) => (
                                <Fragment key={s.id}>
                                    <tr>
                                        <td>{s.candidate_name}</td>
                                        <td>{jobTitle(s.job_id)}</td>
                                        <td>{formatDateTime(s.scheduled_at)}</td>
                                        <td>
                                            <span className={`status-badge ${statusBadgeClass(s.status)}`}>
                                                {STATUS_LABEL[s.status]}
                                            </span>
                                        </td>
                                        <td>
                                            <button
                                                type="button"
                                                className="btn-icon-toggle"
                                                onClick={() =>
                                                    setExpandedSessionId((prev) => (prev === s.id ? null : s.id))
                                                }
                                            >
                                                {expandedSessionId === s.id ? "Ẩn báo cáo" : "Xem báo cáo"}
                                            </button>
                                        </td>
                                    </tr>
                                    {expandedSessionId === s.id && (
                                        <tr>
                                            <td colSpan={5} style={{ padding: "0 0 0.75rem" }}>
                                                <AggregationPanel sessionId={s.id} canTrigger={false} />
                                            </td>
                                        </tr>
                                    )}
                                </Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}