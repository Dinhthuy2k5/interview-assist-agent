import { apiFetch } from "./client";
import type {
    CreateSessionPayload,
    NoteResponse,
    NoteUpsertPayload,
    Session,
    SessionDetail,
    SessionStatus,
} from "../types/session";

export function createSession(payload: CreateSessionPayload): Promise<Session> {
    return apiFetch<Session>("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}

export function listSessions(jobId?: string): Promise<Session[]> {
    const query = jobId ? `?job_id=${jobId}` : "";
    return apiFetch<Session[]>(`/sessions${query}`);
}

export function listMySessions(): Promise<Session[]> {
    return apiFetch<Session[]>("/sessions/mine");
}

export function getSessionDetail(sessionId: string): Promise<SessionDetail> {
    return apiFetch<SessionDetail>(`/sessions/${sessionId}`);
}

export function upsertNote(
    sessionId: string,
    criterionId: string,
    payload: NoteUpsertPayload
): Promise<NoteResponse> {
    return apiFetch<NoteResponse>(`/sessions/${sessionId}/notes/${criterionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}

export function updateSessionStatus(sessionId: string, status: SessionStatus): Promise<Session> {
    return apiFetch<Session>(`/sessions/${sessionId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
    });
}