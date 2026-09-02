import { apiFetch } from "./client";
import type { Decision, DecisionValue } from "../types/decision";

export interface CreateDecisionPayload {
    decision: DecisionValue;
    rationale: string;
}

export function createDecision(sessionId: string, payload: CreateDecisionPayload): Promise<Decision> {
    return apiFetch<Decision>(`/sessions/${sessionId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}

export function listDecisions(sessionId: string): Promise<Decision[]> {
    return apiFetch<Decision[]>(`/sessions/${sessionId}/decisions`);
}