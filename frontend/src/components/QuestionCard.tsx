import { useState } from "react";
import type { Question } from "../types/question";
import { updateQuestion } from "../api/questions";

interface Props {
    question: Question;
    criterionName: string;
    /** % trọng số tương đối trong framework (đã tính từ tổng weight), null nếu chưa
     *  xác định được (không tìm thấy criterion, hoặc framework chưa tải xong). */
    criterionWeightPercent: number | null;
    onUpdated: (question: Question) => void;
}

export default function QuestionCard({
    question,
    criterionName,
    criterionWeightPercent,
    onUpdated,
}: Props) {
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState(question.content);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Sau khi sửa nội dung, backend re-check sensitive filter và có thể trả về
    // is_sensitive_flagged=true ngay trong response PATCH - card cần tự nhận biết
    // trạng thái này để khoá nút duyệt, không chỉ dựa vào dữ liệu ban đầu.
    const blockedByFilter = question.is_sensitive_flagged;

    async function handleSaveContent() {
        const trimmed = draft.trim();
        if (!trimmed) return;
        if (trimmed === question.content.trim()) {
            setEditing(false);
            return;
        }
        setSaving(true);
        setError(null);
        try {
            const updated = await updateQuestion(question.id, { content: trimmed });
            onUpdated(updated);
            setEditing(false);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Lưu câu hỏi thất bại.");
        } finally {
            setSaving(false);
        }
    }

    async function handleToggleApprove() {
        setSaving(true);
        setError(null);
        try {
            const updated = await updateQuestion(question.id, { is_approved: !question.is_approved });
            onUpdated(updated);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Cập nhật trạng thái duyệt thất bại.");
        } finally {
            setSaving(false);
        }
    }

    function handleCancelEdit() {
        setDraft(question.content);
        setEditing(false);
        setError(null);
    }

    return (
        <div className="question-card">
            <div className="question-card-header">
                <div>
                    <p className="question-criterion">{criterionName}</p>
                    <p className="question-weight">
                        {criterionWeightPercent !== null
                            ? `Trọng số ${criterionWeightPercent}% trong framework`
                            : "Trọng số: chưa xác định"}
                    </p>
                </div>
                <span className={`status-badge ${question.is_approved ? "parsed" : "pending"}`}>
                    {question.is_approved ? "Đã duyệt" : "Chờ duyệt"}
                </span>
            </div>

            {blockedByFilter && (
                <div className="notice notice-error">
                    Câu hỏi đang bị đánh dấu nhạy cảm
                    {question.sensitive_flag_reason ? `: ${question.sensitive_flag_reason}` : ""}. Sửa nội
                    dung để bỏ đánh dấu trước khi duyệt.
                </div>
            )}

            {editing ? (
                <>
                    <textarea
                        className="question-textarea"
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        rows={3}
                        autoFocus
                    />
                    <div className="question-actions">
                        <button className="btn" onClick={handleSaveContent} disabled={saving || !draft.trim()}>
                            {saving ? "Đang lưu..." : "Lưu"}
                        </button>
                        <button className="btn btn-secondary" onClick={handleCancelEdit} disabled={saving}>
                            Hủy
                        </button>
                    </div>
                </>
            ) : (
                <>
                    <p className="question-content">{question.content}</p>
                    <p className="question-rationale">Vì sao hỏi câu này: {question.rationale}</p>
                    <div className="question-actions">
                        <button className="btn btn-secondary" onClick={() => setEditing(true)} disabled={saving}>
                            Sửa nội dung
                        </button>
                        <button
                            className="btn"
                            onClick={handleToggleApprove}
                            disabled={saving || (!question.is_approved && blockedByFilter)}
                            title={
                                !question.is_approved && blockedByFilter
                                    ? "Không thể duyệt khi câu hỏi còn bị đánh dấu nhạy cảm"
                                    : undefined
                            }
                        >
                            {question.is_approved ? "Bỏ duyệt" : "Duyệt câu hỏi"}
                        </button>
                    </div>
                </>
            )}

            {question.generated_by === "human_edited" && !editing && (
                <p className="question-meta">Đã chỉnh sửa bởi người dùng</p>
            )}
            {error && (
                <div className="notice notice-error" style={{ marginTop: "0.5rem", marginBottom: 0 }}>
                    {error}
                </div>
            )}
        </div>
    );
}