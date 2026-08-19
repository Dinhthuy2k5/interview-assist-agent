export interface CriterionSummary {
    criterion_id: string;
    criterion_name: string;
    scores: number[];
    average: number | null;
    has_conflict: boolean;
    conflict_type: "rule_based" | "embedding" | null;
    semantic_note: string | null;
    missing_interviewer_labels: string[];
}

export interface AggregationReport {
    id: string;
    session_id: string;
    per_criterion_summary: CriterionSummary[];
    overall_score: number | null;
    overall_recommendation: string;
    rationale_trace: string;
}