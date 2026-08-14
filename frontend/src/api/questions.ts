import { apiFetch } from "./client";
import type { Question, QuestionUpdatePayload } from "../types/question";

export function generateQuestions(jobId: string): Promise<Question[]> {
    return apiFetch<Question[]>(`/jobs/${jobId}/questions/generate`, { method: "POST" });
}

export function listQuestions(jobId: string): Promise<Question[]> {
    return apiFetch<Question[]>(`/jobs/${jobId}/questions`);
}

export function updateQuestion(
    questionId: string,
    payload: QuestionUpdatePayload
): Promise<Question> {
    return apiFetch<Question>(`/questions/${questionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}