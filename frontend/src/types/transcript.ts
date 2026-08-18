export type TranscriptStatus = "pending" | "processing" | "completed" | "failed";

export interface Transcript {
    id: string;
    session_id: string;
    text: string | null;
    status: TranscriptStatus;
    retention_expiry: string;
}