import { useEffect, useState } from "react";
import { createSession, listSessions } from "../api/sessions";
import { listJobs } from "../api/jobs";
import { listUsers } from "../api/users";
import type { Job } from "../types/job";
import type { Session } from "../types/session";
import type { User } from "../types/user";

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

export default function SessionManagePage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [interviewers, setInterviewers] = useState<User[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

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

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (selectedInterviewers.length === 0) {
            setSubmitError("Chọn ít nhất 1 interviewer tham gia.");
            return;
        }
        setSubmitting(true);
        setSubmitError(null);
        try {
            await createSession({
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
            load();
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
            <h1 className="page-heading">Phiên phỏng vấn</h1>
            <p className="page-description">
                Tạo phiên phỏng vấn cho ứng viên và gán interviewer tham gia. Mỗi interviewer ghi
                note/điểm độc lập, không thấy note của người khác cho tới khi có bước tổng hợp
                (sprint sau).
            </p>

            {!loading && jobs.length === 0 && (
                <div className="notice notice-warning">
                    Chưa có job nào - tạo job trước ở tab "Vị trí &amp; JD".
                </div>
            )}
            {!loading && interviewers.length === 0 && (
                <div className="notice notice-warning">
                    Chưa có tài khoản Interviewer nào - tạo ở tab "Người dùng".
                </div>
            )}

            <div className="card">
                <h3 style={{ marginTop: 0, fontSize: "1rem" }}>Tạo phiên phỏng vấn mới</h3>
                <form onSubmit={handleSubmit}>
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

                    <div className="field">
                        <label htmlFor="candidate-info">Thông tin thêm (tuỳ chọn)</label>
                        <textarea
                            id="candidate-info"
                            rows={2}
                            value={candidateInfo}
                            onChange={(e) => setCandidateInfo(e.target.value)}
                            placeholder="CV, kinh nghiệm nổi bật, ghi chú trước phỏng vấn..."
                        />
                    </div>

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

            <h2 className="page-heading" style={{ fontSize: "1.15rem", marginTop: "2rem" }}>
                Danh sách phiên
            </h2>
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
                            </tr>
                        </thead>
                        <tbody>
                            {sessions.map((s) => (
                                <tr key={s.id}>
                                    <td>{s.candidate_name}</td>
                                    <td>{jobTitle(s.job_id)}</td>
                                    <td>{formatDateTime(s.scheduled_at)}</td>
                                    <td>
                                        <span className={`status-badge ${statusBadgeClass(s.status)}`}>
                                            {STATUS_LABEL[s.status]}
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