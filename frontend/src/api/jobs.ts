import { API_BASE_URL, apiFetch } from "./client";
import type { Job } from "../types/job";

export interface CreateJobParams {
    title: string;
    level: string;
    frameworkId: string;
    createdBy: string;
    file: File;
}

export async function createJob(params: CreateJobParams): Promise<Job> {
    const formData = new FormData();
    formData.append("title", params.title);
    formData.append("level", params.level);
    formData.append("framework_id", params.frameworkId);
    formData.append("created_by", params.createdBy);
    formData.append("file", params.file);

    // Không set Content-Type thủ công cho multipart - trình duyệt tự thêm
    // boundary đúng, set tay sẽ làm hỏng request.
    const response = await fetch(`${API_BASE_URL}/jobs`, {
        method: "POST",
        body: formData,
    });
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`Tạo job thất bại (${response.status}): ${body}`);
    }
    return response.json();
}

export function updateJobText(jobId: string, jdText: string): Promise<Job> {
    return apiFetch<Job>(`/jobs/${jobId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jd_text: jdText }),
    });
}