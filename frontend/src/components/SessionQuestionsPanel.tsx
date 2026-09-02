import { useEffect, useState } from "react";
import { getSessionDetail } from "../api/sessions";
import type { QuestionForSession } from "../types/session";
import { parseRubric } from "../utils/rubric";

interface Props {
    sessionId: string;
}

export default function SessionQuestionsPanel({ sessionId }: Props) {
    const [questions, setQuestions] = useState<QuestionForSession[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setLoadError(null);
        getSessionDetail(sessionId)
            .then((detail) => setQuestions(detail.questions))
            .catch(() => setLoadError("Không tải được câu hỏi phỏng vấn."))
            .finally(() => setLoading(false));
    }, [sessionId]);

    if (loading) {
        return <p className="field-hint">Đang tải câu hỏi...</p>;
    }
    if (loadError) {
        return <div className="notice notice-error">{loadError}</div>;
    }
    if (questions.length === 0) {
        return <div className="notice notice-warning">Chưa có câu hỏi nào được duyệt cho job này.</div>;
    }

    return (
        <div className="question-list">
            {questions.map((q) => {
                const levels = parseRubric(q.scoring_rubric);
                return (
                    <div key={q.id} className="question-card">
                        <p className="question-criterion">{q.criterion_name}</p>
                        <p className="question-content">{q.content}</p>
                        <div className="rubric-table" style={{ borderTop: "none", paddingTop: 0 }}>
                            {levels.map((l, i) => (
                                <div className="rubric-row" key={i}>
                                    {l.level && <span className="rubric-level">{l.level}</span>}
                                    <span className="rubric-text">{l.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}