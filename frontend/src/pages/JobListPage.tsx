import { useEffect, useState } from "react";
import { closeJob, listJobs, type JobStatusFilter } from "../api/jobs";
import type { Job } from "../types/job";

const FILTERS: { value: JobStatusFilter; label: string }[] = [
    { value: "open", label: "Đang tuyển" },
    { value: "closed", label: "Đã đóng" },
    { value: "all", label: "Tất cả" },
];

export default function JobListPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [filter, setFilter] = useState<JobStatusFilter>("open");
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [closingId, setClosingId] = useState<string | null>(null);

    function load() {
        setLoading(true);
        setLoadError(null);
        listJobs(filter)
            .then(setJobs)
            .catch(() => setLoadError("Không tải được danh sách job."))
            .finally(() => setLoading(false));
    }

    useEffect(load, [filter]);

    async function handleClose(jobId: string) {
        setClosingId(jobId);
        setLoadError(null);
        try {
            await closeJob(jobId);
            load();
        } catch {
            setLoadError("Đóng tuyển thất bại, thử lại.");
        } finally {
            setClosingId(null);
        }
    }

    return (
        <div className="page-content">
            <h1 className="page-heading">Danh sách job</h1>
            <p className="page-description">
                Job tự chuyển "Đã đóng" khi qua hạn nộp hồ sơ, hoặc bạn có thể đóng tuyển tay bất kỳ
                lúc nào (ví dụ đã tuyển đủ người trước hạn).
            </p>

            <nav className="topbar-nav" style={{ marginBottom: "1.25rem" }}>
                {FILTERS.map((f) => (
                    <button
                        key={f.value}
                        type="button"
                        className={`nav-link ${filter === f.value ? "is-active" : ""}`}
                        onClick={() => setFilter(f.value)}
                    >
                        {f.label}
                    </button>
                ))}
            </nav>

            {loadError && <div className="notice notice-error">{loadError}</div>}

            {loading ? (
                <p className="field-hint">Đang tải...</p>
            ) : jobs.length === 0 ? (
                <div className="notice notice-warning">Không có job nào ở trạng thái này.</div>
            ) : (
                <div className="card">
                    <table className="user-table">
                        <thead>
                            <tr>
                                <th>Vị trí</th>
                                <th>Cấp độ</th>
                                <th>Hạn nộp hồ sơ</th>
                                <th>Trạng thái</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map((j) => (
                                <tr key={j.id}>
                                    <td>{j.title}</td>
                                    <td>{j.level}</td>
                                    <td>{j.application_deadline ?? "Không giới hạn"}</td>
                                    <td>
                                        <span
                                            className={`status-badge ${j.status === "open" ? "parsed" : "pending"}`}
                                        >
                                            {j.status === "open" ? "Đang tuyển" : "Đã đóng"}
                                        </span>
                                    </td>
                                    <td>
                                        {j.status === "open" && (
                                            <button
                                                type="button"
                                                className="btn btn-secondary"
                                                onClick={() => handleClose(j.id)}
                                                disabled={closingId === j.id}
                                            >
                                                {closingId === j.id ? "Đang đóng..." : "Đóng tuyển"}
                                            </button>
                                        )}
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