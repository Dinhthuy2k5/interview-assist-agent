import { useState } from "react";
import type { Job } from "../types/job";
import { updateJobText } from "../api/jobs";

interface Props {
    job: Job;
    onUpdated: (job: Job) => void;
}

export default function JdTextReview({ job, onUpdated }: Props) {
    const [text, setText] = useState(job.jd_text ?? "");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const needsReview = job.jd_parse_status === "needs_review";

    async function handleSave() {
        setSaving(true);
        setError(null);
        try {
            const updated = await updateJobText(job.id, text);
            onUpdated(updated);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Lỗi không xác định");
        } finally {
            setSaving(false);
        }
    }

    return (
        <div style={{ marginTop: "1rem", padding: "1rem", border: "1px solid #ccc", borderRadius: 8 }}>
            <p style={{ margin: 0, marginBottom: "0.5rem" }}>
                Trạng thái parse:{" "}
                <strong style={{ color: needsReview ? "#b45309" : "#15803d" }}>
                    {job.jd_parse_status}
                </strong>
                {needsReview && " — hệ thống extract text không chắc chắn, vui lòng xem lại và sửa."}
            </p>
            <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={10}
                style={{ width: "100%", fontFamily: "monospace", fontSize: "0.9rem" }}
            />
            <div style={{ marginTop: "0.5rem" }}>
                <button onClick={handleSave} disabled={saving}>
                    {saving ? "Đang lưu..." : "Lưu jd_text"}
                </button>
                {error && <p style={{ color: "crimson" }}>{error}</p>}
            </div>
        </div>
    );
}