import { useEffect, useState } from "react";
import type { CompetencyFramework } from "../types/framework";
import type { Job } from "../types/job";
import type { Question } from "../types/question";
import { generateQuestions, listQuestions } from "../api/questions";
import QuestionCard from "./QuestionCard";

interface Props {
    job: Job;
    framework: CompetencyFramework | null;
}

export default function QuestionGenPanel({ job, framework }: Props) {
    const [questions, setQuestions] = useState<Question[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [generating, setGenerating] = useState(false);
    const [generateError, setGenerateError] = useState<string | null>(null);
    const [hasGenerated, setHasGenerated] = useState(false);

    useEffect(() => {
        setLoading(true);
        setLoadError(null);
        listQuestions(job.id)
            .then(setQuestions)
            .catch((e) => setLoadError(e instanceof Error ? e.message : "Không tải được câu hỏi."))
            .finally(() => setLoading(false));
    }, [job.id]);

    async function handleGenerate() {
        setGenerating(true);
        setGenerateError(null);
        try {
            const generated = await generateQuestions(job.id);
            setQuestions(generated);
            setHasGenerated(true);
        } catch (e) {
            setGenerateError(e instanceof Error ? e.message : "Sinh câu hỏi thất bại, thử lại.");
        } finally {
            setGenerating(false);
        }
    }

    function handleQuestionUpdated(updated: Question) {
        setQuestions((prev) => prev.map((q) => (q.id === updated.id ? updated : q)));
    }

    function criterion(criterionId: string) {
        return framework?.criteria.find((c) => c.id === criterionId) ?? null;
    }

    // weight trong DB là trọng số tương đối (vd. 1.5, 1 - không phải thang 0-100 sẵn),
    // nên không thể in thẳng kèm dấu "%". Tính % thực tế dựa trên tổng weight của cả
    // framework để phản ánh đúng tầm quan trọng tương đối giữa các tiêu chí.
    const totalWeight = framework?.criteria.reduce((sum, c) => sum + c.weight, 0) ?? 0;

    function criterionWeightPercent(criterionId: string): number | null {
        const c = criterion(criterionId);
        if (!c || totalWeight <= 0) return null;
        return Math.round((c.weight / totalWeight) * 1000) / 10;
    }

    const alreadyHasQuestions = questions.length > 0;

    return (
        <div className="card" style={{ marginTop: "1.25rem" }}>
            <div className="question-panel-header">
                <div>
                    <h2 className="question-panel-title">Câu hỏi phỏng vấn</h2>
                    <p className="field-hint">
                        Agent sinh 1 câu hỏi cho mỗi tiêu chí trong khung năng lực, dựa trên JD đã xác nhận.
                        Xem lại và duyệt từng câu trước khi dùng trong buổi phỏng vấn.
                    </p>
                </div>
                <button className="btn" onClick={handleGenerate} disabled={generating}>
                    {generating ? "Đang sinh câu hỏi..." : alreadyHasQuestions ? "Sinh lại" : "Sinh câu hỏi"}
                </button>
            </div>

            {alreadyHasQuestions && (
                <p className="field-hint" style={{ marginTop: "-0.75rem", marginBottom: "1rem" }}>
                    Lưu ý: "Sinh lại" hiện tạo thêm một bộ câu hỏi mới chứ chưa thay thế bộ cũ ở backend -
                    dùng thận trọng để tránh trùng lặp.
                </p>
            )}

            {loadError && <div className="notice notice-error">{loadError}</div>}
            {generateError && <div className="notice notice-error">{generateError}</div>}

            {loading ? (
                <p className="field-hint">Đang tải câu hỏi...</p>
            ) : questions.length === 0 ? (
                <div className="notice notice-warning">
                    {hasGenerated
                        ? "Không có câu hỏi nào được tạo ra - có thể toàn bộ đã bị lọc do nội dung nhạy cảm. Kiểm tra lại framework hoặc JD."
                        : 'Chưa có câu hỏi nào. Bấm "Sinh câu hỏi" để agent tạo câu hỏi theo từng tiêu chí trong khung năng lực.'}
                </div>
            ) : (
                <div className="question-list">
                    {questions.map((q) => {
                        const c = criterion(q.criterion_id);
                        return (
                            <QuestionCard
                                key={q.id}
                                question={q}
                                criterionName={c?.name ?? "Tiêu chí (không xác định)"}
                                criterionWeightPercent={criterionWeightPercent(q.criterion_id)}
                                onUpdated={handleQuestionUpdated}
                            />
                        );
                    })}
                </div>
            )}
        </div>
    );
}