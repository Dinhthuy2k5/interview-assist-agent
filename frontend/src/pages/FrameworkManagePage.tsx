import { useEffect, useState } from "react";
import type { CompetencyFramework } from "../types/framework";
import { createFramework, listFrameworks } from "../api/frameworks";
import FrameworkCard from "../components/FrameworkCard";

interface CriterionDraft {
    name: string;
    weight: string;
    scoring_rubric: string;
}

const EMPTY_CRITERION: CriterionDraft = { name: "", weight: "1", scoring_rubric: "" };

export default function FrameworkManagePage() {
    const [frameworks, setFrameworks] = useState<CompetencyFramework[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const [showCreateForm, setShowCreateForm] = useState(false);
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [criteria, setCriteria] = useState<CriterionDraft[]>([{ ...EMPTY_CRITERION }]);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);

    function loadFrameworks() {
        setLoading(true);
        setLoadError(null);
        listFrameworks()
            .then((data) => {
                setFrameworks(data);
                setSelectedId((prev) => prev ?? data[0]?.id ?? null);
            })
            .catch(() => setLoadError("Không tải được danh sách framework."))
            .finally(() => setLoading(false));
    }

    useEffect(loadFrameworks, []);

    function updateCriterion(index: number, field: keyof CriterionDraft, value: string) {
        setCriteria((prev) => prev.map((c, i) => (i === index ? { ...c, [field]: value } : c)));
    }

    function addCriterionRow() {
        setCriteria((prev) => [...prev, { ...EMPTY_CRITERION }]);
    }

    function removeCriterionRow(index: number) {
        setCriteria((prev) => prev.filter((_, i) => i !== index));
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        const validCriteria = criteria.filter((c) => c.name.trim() && c.scoring_rubric.trim());
        if (validCriteria.length === 0) {
            setSubmitError("Cần ít nhất 1 tiêu chí có đủ tên và rubric.");
            return;
        }

        setSubmitting(true);
        setSubmitError(null);
        try {
            const created = await createFramework({
                name,
                description: description || null,
                criteria: validCriteria.map((c) => ({
                    name: c.name,
                    weight: Number(c.weight) || 1,
                    scoring_rubric: c.scoring_rubric,
                })),
            });
            setName("");
            setDescription("");
            setCriteria([{ ...EMPTY_CRITERION }]);
            setShowCreateForm(false);
            loadFrameworks();
            setSelectedId(created.id);
        } catch (e) {
            setSubmitError(e instanceof Error ? e.message : "Tạo framework thất bại.");
        } finally {
            setSubmitting(false);
        }
    }

    const selectedFramework = frameworks.find((f) => f.id === selectedId) ?? null;

    return (
        <div className="page-content">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
                <div>
                    <h1 className="page-heading">Khung năng lực</h1>
                    <p className="page-description" style={{ marginBottom: showCreateForm ? "1.5rem" : 0 }}>
                        Định nghĩa trước bộ tiêu chí dùng chung cho nhiều vị trí — mỗi vị trí sẽ chọn 1
                        khung năng lực để sinh câu hỏi phỏng vấn theo đúng bộ tiêu chí đó.
                    </p>
                </div>
                <button type="button" className="btn" onClick={() => setShowCreateForm((v) => !v)}>
                    {showCreateForm ? "Đóng" : "+ Tạo khung năng lực mới"}
                </button>
            </div>

            {showCreateForm && (
                <div className="card" style={{ marginBottom: "1.5rem" }}>
                    <h3 style={{ marginTop: 0, fontSize: "1rem" }}>Tạo khung năng lực mới</h3>
                    <form onSubmit={handleSubmit}>
                        <div className="form-grid-2">
                            <div className="field">
                                <label htmlFor="fw-name">Tên khung năng lực</label>
                                <input
                                    id="fw-name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="VD: Backend Engineer"
                                    required
                                />
                            </div>

                            <div className="field">
                                <label htmlFor="fw-desc">Mô tả (tuỳ chọn)</label>
                                <input
                                    id="fw-desc"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="Áp dụng cho vị trí backend level junior-mid"
                                />
                            </div>
                        </div>

                        <div className="field">
                            <label>Tiêu chí</label>
                            {criteria.map((c, i) => (
                                <div key={i} className="criterion-row">
                                    <input
                                        value={c.name}
                                        onChange={(e) => updateCriterion(i, "name", e.target.value)}
                                        placeholder="Tên tiêu chí (VD: Problem Solving)"
                                        className="criterion-row-name"
                                    />
                                    <input
                                        value={c.weight}
                                        onChange={(e) => updateCriterion(i, "weight", e.target.value)}
                                        placeholder="Trọng số"
                                        type="number"
                                        step="0.1"
                                        className="criterion-row-weight"
                                    />
                                    <textarea
                                        value={c.scoring_rubric}
                                        onChange={(e) => updateCriterion(i, "scoring_rubric", e.target.value)}
                                        placeholder="Rubric chấm điểm 1-5"
                                        rows={2}
                                        className="criterion-row-rubric"
                                    />
                                    <button
                                        type="button"
                                        className="btn-icon-remove"
                                        onClick={() => removeCriterionRow(i)}
                                        disabled={criteria.length === 1}
                                        title="Xoá tiêu chí này"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ))}
                            <button type="button" className="btn btn-secondary" onClick={addCriterionRow}>
                                + Thêm tiêu chí
                            </button>
                        </div>

                        <button className="btn" type="submit" disabled={submitting} style={{ marginTop: "0.5rem" }}>
                            {submitting ? "Đang tạo..." : "Tạo khung năng lực"}
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
            ) : frameworks.length === 0 ? (
                <div className="notice notice-warning">Chưa có khung năng lực nào.</div>
            ) : (
                <div className="session-workspace">
                    <div className="session-list-col">
                        {frameworks.map((f) => (
                            <button
                                key={f.id}
                                type="button"
                                className={`session-list-item ${selectedId === f.id ? "is-selected" : ""}`}
                                onClick={() => setSelectedId(f.id)}
                            >
                                <span className="session-list-name">{f.name}</span>
                                <span className="session-list-meta">
                                    {f.criteria.length} tiêu chí
                                    {f.description ? ` · ${f.description}` : ""}
                                </span>
                            </button>
                        ))}
                    </div>

                    <div className="session-detail-col">
                        {selectedFramework ? (
                            <FrameworkCard framework={selectedFramework} />
                        ) : (
                            <div className="detail-placeholder">
                                Chọn 1 khung năng lực bên trái để xem chi tiết tiêu chí.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}