export const API_BASE_URL = "http://localhost:8000";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`API error ${response.status}: ${body}`);
    }
    return response.json() as Promise<T>;
}