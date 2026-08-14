import type { Question, QuestionUpdatePayload } from "../types/question";

// Giả định cùng base URL với các api/*.ts khác trong dự án (localhost:8000 theo
// thông báo lỗi ở JobUploadPage). Nếu bạn có một hằng số API_BASE_URL dùng chung
// (vd. trong api/client.ts), thay dòng dưới bằng import từ đó cho nhất quán.
const API_BASE = "http://localhost:8000";

async function extractErrorDetail(res: Response): Promise<string | null> {
    try {
        const data = await res.json();
        return typeof data?.detail === "string" ? data.detail : null;
    } catch {
        return null;
    }
}

export async function generateQuestions(jobId: string): Promise<Question[]> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/questions/generate`, {
        method: "POST",
    });
    if (!res.ok) {
        const detail = await extractErrorDetail(res);
        throw new Error(detail ?? "Sinh câu hỏi thất bại, thử lại.");
    }
    return res.json();
}

export async function listQuestions(jobId: string): Promise<Question[]> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/questions`);
    if (!res.ok) {
        const detail = await extractErrorDetail(res);
        throw new Error(detail ?? "Không tải được danh sách câu hỏi.");
    }
    return res.json();
}

export async function updateQuestion(
    questionId: string,
    payload: QuestionUpdatePayload
): Promise<Question> {
    const res = await fetch(`${API_BASE}/questions/${questionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const detail = await extractErrorDetail(res);
        throw new Error(detail ?? "Cập nhật câu hỏi thất bại.");
    }
    return res.json();
}