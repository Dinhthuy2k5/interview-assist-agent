import { API_BASE_URL, apiFetch, getStoredToken } from "./client";
import type { Job, JobStatus } from "../types/job";

export interface CreateJobParams {
    title: string;
    level: string;
    frameworkId: string;
    file: File;
    applicationDeadline?: string; // "YYYY-MM-DD", để trống = không giới hạn
}

export async function createJob(params: CreateJobParams): Promise<Job> {
    const formData = new FormData();
    formData.append("title", params.title);
    formData.append("level", params.level);
    formData.append("framework_id", params.frameworkId);
    formData.append("file", params.file);
    if (params.applicationDeadline) {
        formData.append("application_deadline", params.applicationDeadline);
    }

    const token = getStoredToken();
    const headers = new Headers();
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    // Không set Content-Type thủ công cho multipart - trình duyệt tự thêm
    // boundary đúng, set tay sẽ làm hỏng request.
    const response = await fetch(`${API_BASE_URL}/jobs`, {
        method: "POST",
        headers,
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

export type JobStatusFilter = "all" | JobStatus;

export function listJobs(status: JobStatusFilter = "all"): Promise<Job[]> {
    return apiFetch<Job[]>(`/jobs?status=${status}`);
}

export function closeJob(jobId: string): Promise<Job> {
    return apiFetch<Job>(`/jobs/${jobId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_closed: true }),
    });
}