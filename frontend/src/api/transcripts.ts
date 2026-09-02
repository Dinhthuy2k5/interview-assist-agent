import { API_BASE_URL, getStoredAccessToken } from "./client";
import type { Transcript } from "../types/transcript";

function authHeaders(): Headers {
    const token = getStoredAccessToken();
    const headers = new Headers();
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
}

export async function uploadTranscriptAudio(sessionId: string, file: File): Promise<Transcript> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/transcript`, {
        method: "POST",
        headers: authHeaders(),
        body: formData,
    });
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`Tải lên audio thất bại (${response.status}): ${body}`);
    }
    return response.json();
}

/** Trả về null nếu session chưa có transcript (404 - trạng thái BÌNH THƯỜNG, không
 * phải lỗi) - không dùng apiFetch ở đây vì nó ném Error cho mọi !response.ok, không
 * phân biệt được "chưa có" với lỗi thật (403, 500...). */
export async function getTranscript(sessionId: string): Promise<Transcript | null> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/transcript`, {
        headers: authHeaders(),
    });
    if (response.status === 404) {
        return null;
    }
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`Không tải được transcript (${response.status}): ${body}`);
    }
    return response.json();
}