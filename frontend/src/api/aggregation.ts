import { API_BASE_URL, apiFetch, getStoredToken } from "./client";
import type { AggregationReport, RawNote } from "../types/aggregation";

export function triggerAggregate(sessionId: string): Promise<AggregationReport> {
    return apiFetch<AggregationReport>(`/sessions/${sessionId}/aggregate`, { method: "POST" });
}

export function getSessionNotes(sessionId: string): Promise<RawNote[]> {
    return apiFetch<RawNote[]>(`/sessions/${sessionId}/notes`);
}

/** Trả về null nếu session chưa được tổng hợp (404 - trạng thái BÌNH THƯỜNG) -
 * không dùng apiFetch để tự phân biệt được với lỗi thật (403, 500...). */
export async function getAggregationReport(sessionId: string): Promise<AggregationReport | null> {
    const token = getStoredToken();
    const headers = new Headers();
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/aggregation`, { headers });
    if (response.status === 404) {
        return null;
    }
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`Không tải được báo cáo tổng hợp (${response.status}): ${body}`);
    }
    return response.json();
}