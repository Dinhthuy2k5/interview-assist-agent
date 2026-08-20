import { useEffect, useState } from "react";
import { getAggregationReport, getSessionNotes, triggerAggregate } from "../api/aggregation";
import type { AggregationReport, RawNote } from "../types/aggregation";

interface Props {
    sessionId: string;
    /** HR bấm được nút tổng hợp/tổng hợp lại; Council chỉ đọc, không thấy nút này -
     * khớp đúng quyền backend (POST /aggregate vẫn hr_admin-only). */
    canTrigger: boolean;
}

function recommendationBadgeClass(recommendation: string): string {
    if (recommendation === "Đề xuất tuyển") return "parsed";
    if (recommendation === "Không đề xuất") return "needs_review";
    return "pending";
}

export default function AggregationPanel({ sessionId, canTrigger }: Props) {
    const [report, setReport] = useState<AggregationReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [aggregating, setAggregating] = useState(false);
    const [aggregateError, setAggregateError] = useState<string | null>(null);
    const [rawNotes, setRawNotes] = useState<RawNote[] | null>(null);
    const [loadingNotes, setLoadingNotes] = useState(false);
    const [notesError, setNotesError] = useState<string | null>(null);

    function load() {
        setLoading(true);
        setLoadError(null);
        getAggregationReport(sessionId)
            .then(setReport)
            .catch(() => setLoadError("Không tải được báo cáo tổng hợp."))
            .finally(() => setLoading(false));
    }

    useEffect(load, [sessionId]);

    async function handleAggregate() {
        setAggregating(true);
        setAggregateError(null);
        try {
            const result = await triggerAggregate(sessionId);
            setReport(result);
        } catch (err) {
            setAggregateError(err instanceof Error ? err.message : "Tổng hợp thất bại, thử lại.");
        } finally {
            setAggregating(false);
        }
    }

    async function handleShowNotes() {
        if (rawNotes) {
            setRawNotes(null); // toggle ẩn nếu đã hiện
            return;
        }
        setLoadingNotes(true);
        setNotesError(null);
        try {
            const notes = await getSessionNotes(sessionId);
            setRawNotes(notes);
        } catch (err) {
            setNotesError(err instanceof Error ? err.message : "Không tải được note gốc.");
        } finally {
            setLoadingNotes(false);
        }
    }

    if (loading) {
        return (
            <div className="aggregation-panel">
                <p className="field-hint" style={{ margin: 0 }}>
                    Đang tải báo cáo tổng hợp...
                </p>
            </div>
        );
    }

    return (
        <div className="aggregation-panel">
            <div className="aggregation-panel-header">
                <p className="transcript-panel-title" style={{ margin: 0 }}>
                    Báo cáo tổng hợp đánh giá
                </p>
                {canTrigger && (
                    <button
                        className="btn btn-secondary"
                        type="button"
                        onClick={handleAggregate}
                        disabled={aggregating}
                    >
                        {aggregating ? "Đang tổng hợp..." : report ? "Tổng hợp lại" : "Tổng hợp đánh giá"}
                    </button>
                )}
            </div>

            {loadError && <div className="notice notice-error">{loadError}</div>}
            {aggregateError && <div className="notice notice-error">{aggregateError}</div>}

            {!report ? (
                <p className="field-hint" style={{ margin: 0 }}>
                    {canTrigger
                        ? "Chưa tổng hợp - bấm nút bên trên khi các interviewer đã ghi note (không bắt buộc đủ mọi người)."
                        : "HR chưa tổng hợp đánh giá cho session này."}
                </p>
            ) : (
                <div>
                    <div className="aggregation-overall">
                        <span className={`status-badge ${recommendationBadgeClass(report.overall_recommendation)}`}>
                            {report.overall_recommendation}
                        </span>
                        {report.overall_score !== null && (
                            <span className="aggregation-score">{report.overall_score.toFixed(2)}/5</span>
                        )}
                    </div>

                    <p className="question-rationale" style={{ marginTop: "0.6rem" }}>
                        {report.rationale_trace}
                    </p>

                    <div className="aggregation-criteria-list">
                        {report.per_criterion_summary.map((c) => (
                            <div key={c.criterion_id} className="aggregation-criterion-row">
                                <div className="aggregation-criterion-header">
                                    <span className="question-criterion" style={{ fontSize: "0.86rem" }}>
                                        {c.criterion_name}
                                    </span>
                                    <span className="weight-pill">
                                        {c.average !== null ? `TB ${c.average.toFixed(1)}/5` : "Chưa có điểm"}
                                    </span>
                                </div>

                                {c.has_conflict && (
                                    <div className="notice notice-warning" style={{ marginBottom: "0.5rem" }}>
                                        Đánh giá không đồng nhất giữa các interviewer (
                                        {c.conflict_type === "rule_based" ? "chênh điểm lớn" : "lý do khác biệt"}
                                        ). {c.semantic_note}
                                    </div>
                                )}

                                {c.missing_interviewer_labels.length > 0 && (
                                    <p className="field-hint" style={{ margin: 0 }}>
                                        Chưa ghi note: {c.missing_interviewer_labels.join(", ")}
                                    </p>
                                )}

                                {rawNotes && (
                                    <div className="raw-notes-box">
                                        {rawNotes
                                            .filter((n) => n.criterion_id === c.criterion_id)
                                            .map((n, i) => (
                                                <div key={i} className="raw-note-item">
                                                    <span className="raw-note-label">{n.interviewer_label}</span>
                                                    <span className="raw-note-score">
                                                        {n.score !== null ? `${n.score}/5` : "Chưa chấm"}
                                                    </span>
                                                    <p className="raw-note-text">
                                                        {n.note_text || "(không có ghi chú)"}
                                                    </p>
                                                </div>
                                            ))}
                                        {rawNotes.filter((n) => n.criterion_id === c.criterion_id).length === 0 && (
                                            <p className="field-hint" style={{ margin: 0 }}>
                                                Chưa có note nào cho tiêu chí này.
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="question-actions" style={{ marginTop: "0.85rem" }}>
                        <button type="button" className="btn-icon-toggle" onClick={handleShowNotes} disabled={loadingNotes}>
                            {loadingNotes ? "Đang tải..." : rawNotes ? "Ẩn note gốc" : "Xem note gốc"}
                        </button>
                    </div>
                    {notesError && (
                        <div className="notice notice-error" style={{ marginTop: "0.6rem", marginBottom: 0 }}>
                            {notesError}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}