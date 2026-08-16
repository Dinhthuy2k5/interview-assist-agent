export type SessionStatus = "scheduled" | "in_progress" | "completed";

export interface Session {
    id: string;
    job_id: string;
    candidate_name: string;
    candidate_info: string | null;
    scheduled_at: string;
    status: SessionStatus;
}

export interface QuestionForSession {
    id: string;
    criterion_id: string;
    criterion_name: string;
    scoring_rubric: string;
    content: string;
}

export interface NoteResponse {
    id: string;
    session_id: string;
    criterion_id: string;
    score: number | null;
    note_text: string | null;
}

export interface SessionDetail {
    session: Session;
    questions: QuestionForSession[];
    my_notes: NoteResponse[];
}

export interface CreateSessionPayload {
    job_id: string;
    candidate_name: string;
    candidate_info: string | null;
    scheduled_at: string; // ISO string
    interviewer_ids: string[];
}

export interface NoteUpsertPayload {
    score: number | null;
    note_text: string | null;
}