import { useEffect, useState } from "react";
import { createSession, listSessions } from "../api/sessions";
import { listJobs } from "../api/jobs";
import { listUsers } from "../api/users";
import type { Job } from "../types/job";
import type { Session } from "../types/session";
import type { User } from "../types/user";
import TranscriptPanel from "../components/TranscriptPanel";
import AggregationPanel from "../components/AggregationPanel";
import DecisionPanel from "../components/DecisionPanel";

const STATUS_LABEL: Record<string, string> = {
    scheduled: "Chưa bắt đầu",
    in_progress: "Đang phỏng vấn",
    completed: "Đã hoàn tất",
};

type DetailTab = "transcript" | "aggregation" | "decision";

function statusBadgeClass(status: string): string {
    if (status === "completed") return "parsed";
    if (status === "in_progress") return "needs_review";
    return "pending";
}

function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString("vi-VN", { dateStyle: "medium", timeStyle: "short" });
}

export default function SessionManagePage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [interviewers, setInterviewers] = useState<User[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [detailTab, setDetailTab] = useState<DetailTab>("transcript");

    const [showCreateForm, setShowCreateForm] = useState(false);
    const [jobId, setJobId] = useState("");
    const [candidateName, setCandidateName] = useState("");
    const [candidateInfo, setCandidateInfo] = useState("");
    const [scheduledAt, setScheduledAt] = useState("");
    const [selectedInterviewers, setSelectedInterviewers] = useState<string[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);

    function load() {
        setLoading(true);
        setLoadError(null);
        Promise.all([listJobs("all"), listUsers(), listSessions()])
            .then(([jobsData, usersData, sessionsData]) => {
                setJobs(jobsData);
                setInterviewers(usersData.filter((u) => u.role === "interviewer"));
                setSessions(sessionsData);
                setJobId((prev) => prev || jobsData[0]?.id || "");
            })
            .catch(() => setLoadError("Không tải được dữ liệu."))
            .finally(() => setLoading(false));
    }

    useEffect(load, []);

    function toggleInterviewer(id: string) {
        setSelectedInterviewers((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    }

    function selectSession(id: string) {
        setSelectedSessionId(id);
        setDetailTab("transcript");
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (selectedInterviewers.length === 0) {
            setSubmitError("Chọn ít nhất 1 interviewer tham gia.");
            return;
        }
        setSubmitting(true);
        setSubmitError(null);
        try {
            const created = await createSession({
                job_id: jobId,
                candidate_name: candidateName,
                candidate_info: candidateInfo || null,
                scheduled_at: new Date(scheduledAt).toISOString(),
                interviewer_ids: selectedInterviewers,
            });
            setCandidateName("");
            setCandidateInfo("");
            setScheduledAt("");
            setSelectedInterviewers([]);
            setShowCreateForm(false);
            load();
            selectSession(created.id);
        } catch (e) {
            setSubmitError(e instanceof Error ? e.message : "Tạo phiên phỏng vấn thất bại.");
        } finally {
            setSubmitting(false);
        }
    }

    function jobTitle(id: string): string {
        return jobs.find((j) => j.id === id)?.title ?? "(job không xác định)";
    }

    return (
        <div className="page-content">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
                <div>
                    <h1 className="page-heading">Phiên phỏng vấn</h1>
                    <p className="page-description" style={{ marginBottom: showCreateForm ? "1.5rem" : 0 }}>
                        Tạo phiên phỏng vấn, gán interviewer. Chọn 1 phiên bên trái để xem transcript, báo
                        cáo tổng hợp và quyết định của Hội đồng.
                    </p>
                </div>
                <button type="button" className="btn" onClick={() => setShowCreateForm((v) => !v)}>
                    {showCreateForm ? "Đóng" : "+ Tạo phiên mới"}
                </button>
            </div>

            {showCreateForm && (
                <div className="card" style={{ marginBottom: "1.5rem" }}>
                    <h3 style={{ marginTop: 0, fontSize: "1rem" }}>Tạo phiên phỏng vấn mới</h3>
                    <form onSubmit={handleSubmit}>
                        <div className="form-grid-2">
                            <div className="field">
                                <label htmlFor="session-job">Job</label>
                                <select
                                    id="session-job"
                                    value={jobId}
                                    onChange={(e) => setJobId(e.target.value)}
                                    required
                                    disabled={jobs.length === 0}
                                >
                                    {jobs.map((j) => (
                                        <option key={j.id} value={j.id}>
                                            {j.title}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="field">
                                <label htmlFor="candidate-name">Tên ứng viên</label>
                                <input
                                    id="candidate-name"
                                    value={candidateName}
                                    onChange={(e) => setCandidateName(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-grid-2">
                            <div className="field">
                                <label htmlFor="scheduled-at">Thời gian phỏng vấn</label>
                                <input
                                    id="scheduled-at"
                                    type="datetime-local"
                                    value={scheduledAt}
                                    onChange={(e) => setScheduledAt(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="field">
                                <label htmlFor="candidate-info">Thông tin thêm (tuỳ chọn)</label>
                                <input
                                    id="candidate-info"
                                    value={candidateInfo}
                                    onChange={(e) => setCandidateInfo(e.target.value)}
                                    placeholder="CV, kinh nghiệm nổi bật..."
                                />
                            </div>
                        </div>

                        <div className="field">
                            <label>Interviewer tham gia</label>
                            <div className="interviewer-picker">
                                {interviewers.length === 0 ? (
                                    <p className="field-hint" style={{ margin: 0 }}>
                                        Chưa có interviewer nào để chọn.
                                    </p>
                                ) : (
                                    interviewers.map((u) => (
                                        <label key={u.id} className="interviewer-option">
                                            <input
                                                type="checkbox"
                                                checked={selectedInterviewers.includes(u.id)}
                                                onChange={() => toggleInterviewer(u.id)}
                                            />
                                            {u.full_name}
                                        </label>
                                    ))
                                )}
                            </div>
                        </div>

                        <button
                            className="btn"
                            type="submit"
                            disabled={submitting || jobs.length === 0 || interviewers.length === 0}
                        >
                            {submitting ? "Đang tạo..." : "Tạo phiên phỏng vấn"}
                        </button>
                        {submitError && (
                            <div className="notice notice-error" style={{ marginTop: "1rem", marginBottom: 0 }}>
                                {submitError}
                            </div>
                        )}
                    </form>
                </div>
            )}

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
                                            { key: "transcript", label: "Transcript" },
                                            { key: "aggregation", label: "Báo cáo tổng hợp" },
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

                                {detailTab === "transcript" && <TranscriptPanel sessionId={selectedSessionId} />}
                                {detailTab === "aggregation" && (
                                    <AggregationPanel sessionId={selectedSessionId} canTrigger />
                                )}
                                {detailTab === "decision" && (
                                    <DecisionPanel sessionId={selectedSessionId} canSubmit={false} />
                                )}
                            </>
                        ) : (
                            <div className="detail-placeholder">
                                Chọn 1 phiên phỏng vấn bên trái để xem chi tiết.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}