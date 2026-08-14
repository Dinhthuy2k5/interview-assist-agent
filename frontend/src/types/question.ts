export type GeneratedBy = "agent" | "human_edited";

export interface Question {
    id: string;
    job_id: string;
    criterion_id: string;
    content: string;
    rationale: string;
    generated_by: GeneratedBy;
    is_sensitive_flagged: boolean;
    sensitive_flag_reason: string | null;
    is_approved: boolean;
}

export interface QuestionUpdatePayload {
    content?: string;
    is_approved?: boolean;
}