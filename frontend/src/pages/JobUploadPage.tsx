import { useEffect, useState } from "react";
import type { CompetencyFramework } from "../types/framework";
import type { Job } from "../types/job";
import { listFrameworks } from "../api/frameworks";
import { createJob } from "../api/jobs";
import JdTextReview from "../components/JdTextReview";
import PipelineStepper from "../components/PipelineStepper";
import QuestionGenPanel from "../components/QuestionGenPanel";

const LEVELS = ["fresher", "junior", "senior"];

export default function JobUploadPage() {
    const [frameworks, setFrameworks] = useState<CompetencyFramework[]>([]);
    const [frameworksError, setFrameworksError] = useState<string | null>(null);
    const [title, setTitle] = useState("");
    const [level, setLevel] = useState(LEVELS[1]);
    const [frameworkId, setFrameworkId] = useState("");
    const [applicationDeadline, setApplicationDeadline] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [job, setJob] = useState<Job | null>(null);

    useEffect(() => {
        listFrameworks()
            .then((data) => {
                setFrameworks(data);
                if (data.length > 0) setFrameworkId(data[0].id);
            })
            .catch(() =>
                setFrameworksError(
                    "Không kết nối được tới API. Kiểm tra backend đang chạy ở localhost:8000."
                )
            );
    }, []);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!file || !frameworkId) return;

        setSubmitting(true);
        setSubmitError(null);
        try {
            const created = await createJob({
                title,
                level,
                frameworkId,
                file,
                applicationDeadline: applicationDeadline || undefined,
            });
            setJob(created);
        } catch (e) {
            setSubmitError(e instanceof Error ? e.message : "Tạo job thất bại, thử lại.");
        } finally {
            setSubmitting(false);
        }
    }

    const pipelineStatus = job ? job.jd_parse_status : "idle";

    // Chỉ cho sinh câu hỏi khi JD đã có text và không còn ở trạng thái cần review -
    // tránh sinh câu hỏi từ nội dung extract chưa chắc chắn (needs_review).
    const readyForQuestions = job !== null && job.jd_text !== null && job.jd_parse_status !== "needs_review";
    const jobFramework = job ? frameworks.find((f) => f.id === job.framework_id) ?? null : null;

    return (
        <div className="page-content">
            <h1 className="page-heading">Tải lên mô tả công việc</h1>
            <p className="page-description">
                Chọn khung năng lực trước, hệ thống sẽ dùng đúng bộ tiêu chí đó để sinh câu hỏi
                phỏng vấn ở bước sau.
            </p>

            <PipelineStepper status={pipelineStatus} />

            {frameworksError && <div className="notice notice-error">{frameworksError}</div>}

            {!frameworksError && frameworks.length === 0 && (
                <div className="notice notice-warning">
                    Chưa có Competency Framework nào. Tạo một framework qua{" "}
                    <code>POST /frameworks</code> (Swagger UI ở localhost:8000/docs), rồi tải lại
                    trang này.
                </div>
            )}

            <div className="card">
                <form onSubmit={handleSubmit}>
                    <div className="field">
                        <label htmlFor="title">Tên vị trí</label>
                        <input
                            id="title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="VD: Backend Engineer"
                            required
                        />
                    </div>

                    <div className="field">
                        <label htmlFor="level">Cấp độ</label>
                        <select id="level" value={level} onChange={(e) => setLevel(e.target.value)}>
                            {LEVELS.map((l) => (
                                <option key={l} value={l}>
                                    {l}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="field">
                        <label htmlFor="framework">Khung năng lực</label>
                        <select
                            id="framework"
                            value={frameworkId}
                            onChange={(e) => setFrameworkId(e.target.value)}
                            required
                            disabled={frameworks.length === 0}
                        >
                            {frameworks.map((f) => (
                                <option key={f.id} value={f.id}>
                                    {f.name}
                                </option>
                            ))}
                        </select>
                        <p className="field-hint">Quyết định bộ tiêu chí dùng để sinh câu hỏi sau này.</p>
                    </div>

                    <div className="field">
                        <label htmlFor="deadline">Hạn nộp hồ sơ (tuỳ chọn)</label>
                        <input
                            id="deadline"
                            type="date"
                            value={applicationDeadline}
                            onChange={(e) => setApplicationDeadline(e.target.value)}
                        />
                        <p className="field-hint">Để trống nếu không giới hạn thời gian tuyển.</p>
                    </div>

                    <div className="field">
                        <label htmlFor="file">File JD (.pdf hoặc .docx)</label>
                        <div className="file-input">
                            <input
                                id="file"
                                type="file"
                                accept=".pdf,.docx"
                                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                                required
                            />
                        </div>
                    </div>

                    <button className="btn" type="submit" disabled={submitting || frameworks.length === 0}>
                        {submitting ? "Đang tải lên..." : "Tải lên"}
                    </button>
                </form>

                {submitError && (
                    <div className="notice notice-error" style={{ marginTop: "1rem", marginBottom: 0 }}>
                        {submitError}
                    </div>
                )}
            </div>

            {job && (
                <div style={{ marginTop: "1.25rem" }}>
                    <JdTextReview job={job} onUpdated={setJob} />
                </div>
            )}

            {readyForQuestions && job && <QuestionGenPanel job={job} framework={jobFramework} />}
        </div>
    );
}