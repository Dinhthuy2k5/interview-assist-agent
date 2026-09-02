import { useEffect, useState } from "react";
import { createDecision, listDecisions } from "../api/decisions";
import type { Decision, DecisionValue } from "../types/decision";

interface Props {
    sessionId: string;
    /** Council ghi được quyết định; HR chỉ xem (đúng vai trò "ra quyết định cuối"
     * chỉ thuộc về Council, xem ADR 0001). */
    canSubmit: boolean;
}

const DECISION_LABEL: Record<DecisionValue, string> = {
    hired: "Đề xuất tuyển",
    rejected: "Không tuyển",
    on_hold: "Tạm giữ",
};

function decisionBadgeClass(decision: string): string {
    if (decision === "hired") return "parsed";
    if (decision === "rejected") return "needs_review";
    return "pending";
}

function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString("vi-VN", { dateStyle: "medium", timeStyle: "short" });
}

export default function DecisionPanel({ sessionId, canSubmit }: Props) {
    const [decisions, setDecisions] = useState<Decision[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    const [showForm, setShowForm] = useState(false);
    const [decisionValue, setDecisionValue] = useState<DecisionValue>("hired");
    const [rationale, setRationale] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);

    function load() {
        setLoading(true);
        setLoadError(null);
        listDecisions(sessionId)
            .then(setDecisions)
            .catch(() => setLoadError("Không tải được lịch sử quyết định."))
            .finally(() => setLoading(false));
    }

    useEffect(load, [sessionId]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!rationale.trim()) {
            setSubmitError("Cần nêu lý do quyết định.");
            return;
        }
        setSubmitting(true);
        setSubmitError(null);
        try {
            await createDecision(sessionId, { decision: decisionValue, rationale: rationale.trim() });
            setRationale("");
            setShowForm(false);
            load();
        } catch (err) {
            setSubmitError(err instanceof Error ? err.message : "Ghi quyết định thất bại.");
        } finally {
            setSubmitting(false);
        }
    }

    if (loading) {
        return (
            <div className="aggregation-panel">
                <p className="field-hint" style={{ margin: 0 }}>
                    Đang tải quyết định...
                </p>
            </div>
        );
    }

    const latest = decisions[0] ?? null;
    const history = decisions.slice(1);

    return (
        <div className="aggregation-panel">
            <div className="aggregation-panel-header">
                <p className="transcript-panel-title" style={{ margin: 0 }}>
                    Quyết định tuyển dụng
                </p>
                {canSubmit && (
                    <button type="button" className="btn btn-secondary" onClick={() => setShowForm((v) => !v)}>
                        {showForm ? "Đóng" : latest ? "Ghi quyết định mới" : "Ghi quyết định"}
                    </button>
                )}
            </div>

            {loadError && <div className="notice notice-error">{loadError}</div>}

            {showForm && (
                <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
                    <div className="field">
                        <label htmlFor="decision-value">Quyết định</label>
                        <select
                            id="decision-value"
                            value={decisionValue}
                            onChange={(e) => setDecisionValue(e.target.value as DecisionValue)}
                        >
                            <option value="hired">Đề xuất tuyển</option>
                            <option value="on_hold">Tạm giữ</option>
                            <option value="rejected">Không tuyển</option>
                        </select>
                    </div>
                    <div className="field">
                        <label htmlFor="decision-rationale">Lý do</label>
                        <textarea
                            id="decision-rationale"
                            rows={3}
                            value={rationale}
                            onChange={(e) => setRationale(e.target.value)}
                            placeholder="Nêu rõ lý do, dựa trên báo cáo tổng hợp và note gốc..."
                        />
                    </div>
                    <button className="btn" type="submit" disabled={submitting}>
                        {submitting ? "Đang lưu..." : "Xác nhận quyết định"}
                    </button>
                    {submitError && (
                        <div className="notice notice-error" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
                            {submitError}
                        </div>
                    )}
                </form>
            )}

            {!latest ? (
                <p className="field-hint" style={{ margin: 0 }}>
                    {canSubmit ? 'Chưa có quyết định nào - bấm "Ghi quyết định" ở trên.' : "Hội đồng chưa ra quyết định."}
                </p>
            ) : (
                <div>
                    <div className="aggregation-overall">
                        <span className={`status-badge ${decisionBadgeClass(latest.decision)}`}>
                            {DECISION_LABEL[latest.decision]}
                        </span>
                        <span className="field-hint" style={{ margin: 0 }}>
                            bởi {latest.decided_by_name} · {formatDateTime(latest.created_at)}
                        </span>
                    </div>
                    <p className="question-rationale" style={{ marginTop: "0.6rem" }}>
                        {latest.rationale}
                    </p>

                    {history.length > 0 && (
                        <details style={{ marginTop: "0.85rem" }}>
                            <summary className="field-hint" style={{ cursor: "pointer" }}>
                                Xem lịch sử ({history.length} quyết định trước đó)
                            </summary>
                            <div className="aggregation-criteria-list" style={{ marginTop: "0.6rem" }}>
                                {history.map((d) => (
                                    <div key={d.id} className="aggregation-criterion-row">
                                        <div className="aggregation-criterion-header">
                                            <span className={`status-badge ${decisionBadgeClass(d.decision)}`}>
                                                {DECISION_LABEL[d.decision]}
                                            </span>
                                            <span className="field-hint" style={{ margin: 0 }}>
                                                {d.decided_by_name} · {formatDateTime(d.created_at)}
                                            </span>
                                        </div>
                                        <p className="question-rationale" style={{ margin: 0 }}>
                                            {d.rationale}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </details>
                    )}
                </div>
            )}
        </div>
    );
}