import { useEffect, useState } from "react";
import { getSessionDetail, updateSessionStatus, upsertNote } from "../api/sessions";
import type { SessionDetail } from "../types/session";
import { parseRubric } from "../utils/rubric";
import TranscriptPanel from "./TranscriptPanel";

interface Props {
    sessionId: string;
    onBack: () => void;
}

interface DraftNote {
    score: number | null;
    noteText: string;
}

export default function InterviewSessionCardView({ sessionId, onBack }: Props) {
    const [detail, setDetail] = useState<SessionDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [index, setIndex] = useState(0);
    const [drafts, setDrafts] = useState<Record<string, DraftNote>>({});
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

    useEffect(() => {
        setLoading(true);
        setLoadError(null);
        getSessionDetail(sessionId)
            .then((d) => {
                setDetail(d);
                const initialDrafts: Record<string, DraftNote> = {};
                for (const q of d.questions) {
                    const existing = d.my_notes.find((n) => n.criterion_id === q.criterion_id);
                    initialDrafts[q.criterion_id] = {
                        score: existing?.score ?? null,
                        noteText: existing?.note_text ?? "",
                    };
                }
                setDrafts(initialDrafts);
                // Interviewer mở session lần đầu -> tự chuyển "Đang phỏng vấn", best-effort
                // (không chặn UI nếu lỗi, chỉ là trạng thái hiển thị cho HR theo dõi).
                if (d.session.status === "scheduled") {
                    updateSessionStatus(sessionId, "in_progress").catch(() => { });
                }
            })
            .catch(() => setLoadError("Không tải được session."))
            .finally(() => setLoading(false));
    }, [sessionId]);

    if (loading) {
        return (
            <div className="page-content">
                <p className="field-hint">Đang tải...</p>
            </div>
        );
    }

    if (loadError || !detail) {
        return (
            <div className="page-content">
                <div className="notice notice-error">{loadError ?? "Không có dữ liệu."}</div>
                <button type="button" className="btn btn-secondary" onClick={onBack}>
                    Quay lại danh sách
                </button>
            </div>
        );
    }

    const questions = detail.questions;

    if (questions.length === 0) {
        return (
            <div className="page-content">
                <div className="notice notice-warning">
                    Job này chưa có câu hỏi nào được HR duyệt - liên hệ HR trước khi phỏng vấn.
                </div>
                <button type="button" className="btn btn-secondary" onClick={onBack}>
                    Quay lại danh sách
                </button>
            </div>
        );
    }

    const current = questions[index];
    const draft = drafts[current.criterion_id] ?? { score: null, noteText: "" };
    const levels = parseRubric(current.scoring_rubric);
    const isLast = index === questions.length - 1;

    function updateDraft(patch: Partial<DraftNote>) {
        setDrafts((prev) => ({ ...prev, [current.criterion_id]: { ...draft, ...patch } }));
        setSavedIds((prev) => {
            const next = new Set(prev);
            next.delete(current.criterion_id);
            return next;
        });
    }

    async function saveCurrent(): Promise<boolean> {
        setSaving(true);
        setSaveError(null);
        try {
            await upsertNote(sessionId, current.criterion_id, {
                score: draft.score,
                note_text: draft.noteText || null,
            });
            setSavedIds((prev) => new Set(prev).add(current.criterion_id));
            return true;
        } catch {
            setSaveError("Lưu note thất bại, thử lại.");
            return false;
        } finally {
            setSaving(false);
        }
    }

    async function goTo(newIndex: number) {
        // Tự lưu trước khi chuyển câu - đúng nhu cầu "ghi nhanh, không bị phân tâm",
        // interviewer không phải nhớ bấm Lưu trước khi lật thẻ tiếp theo. Nhưng nếu
        // lưu thất bại, KHÔNG được chuyển câu - nếu không note vừa gõ sẽ mất mà
        // interviewer tưởng đã lưu (đã chuyển sang câu khác).
        const ok = await saveCurrent();
        if (!ok) return;
        setIndex(newIndex);
    }

    async function handleFinish() {
        const ok = await saveCurrent();
        if (!ok) return;
        try {
            await updateSessionStatus(sessionId, "completed");
        } catch {
            // best-effort - không chặn interviewer nếu chỉ lỗi update status
        }
        onBack();
    }

    return (
        <div className="page-content">
            <button
                type="button"
                className="btn-icon-toggle"
                onClick={onBack}
                style={{ marginBottom: "1rem" }}
            >
                ← Danh sách phiên
            </button>

            <h1 className="page-heading">{detail.session.candidate_name}</h1>
            <p className="page-description">
                Tiêu chí {index + 1}/{questions.length} — {current.criterion_name}
            </p>

            <TranscriptPanel sessionId={sessionId} />

            <div className="card">
                <p className="question-content" style={{ fontSize: "1.05rem" }}>
                    {current.content}
                </p>

                <div
                    className="rubric-table"
                    style={{ borderTop: "none", paddingTop: 0, marginBottom: "1.25rem" }}
                >
                    {levels.map((l, i) => (
                        <div className="rubric-row" key={i}>
                            {l.level && <span className="rubric-level">{l.level}</span>}
                            <span className="rubric-text">{l.text}</span>
                        </div>
                    ))}
                </div>

                <div className="field">
                    <label>Điểm (1-5)</label>
                    <div className="score-picker">
                        {[1, 2, 3, 4, 5].map((n) => (
                            <button
                                key={n}
                                type="button"
                                className={`score-btn ${draft.score === n ? "is-selected" : ""}`}
                                onClick={() => updateDraft({ score: n })}
                            >
                                {n}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="field">
                    <label htmlFor="note-text">Ghi chú</label>
                    <textarea
                        id="note-text"
                        rows={4}
                        value={draft.noteText}
                        onChange={(e) => updateDraft({ noteText: e.target.value })}
                        placeholder="Ghi nhanh trong lúc phỏng vấn..."
                    />
                </div>

                <div className="question-actions">
                    <button type="button" className="btn btn-secondary" onClick={saveCurrent} disabled={saving}>
                        {saving ? "Đang lưu..." : savedIds.has(current.criterion_id) ? "Đã lưu ✓" : "Lưu"}
                    </button>
                </div>

                {saveError && (
                    <div className="notice notice-error" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
                        {saveError}
                    </div>
                )}
            </div>

            <div className="question-actions" style={{ marginTop: "1.25rem", justifyContent: "space-between" }}>
                <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => goTo(index - 1)}
                    disabled={index === 0 || saving}
                >
                    ← Câu trước
                </button>
                {isLast ? (
                    <button type="button" className="btn" onClick={handleFinish} disabled={saving}>
                        Hoàn tất phỏng vấn
                    </button>
                ) : (
                    <button type="button" className="btn" onClick={() => goTo(index + 1)} disabled={saving}>
                        Câu tiếp theo →
                    </button>
                )}
            </div>
        </div>
    );
}