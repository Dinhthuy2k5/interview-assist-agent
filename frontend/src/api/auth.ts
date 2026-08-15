import { API_BASE_URL, apiFetch } from "./client";
import type { User } from "../types/user";

export interface LoginResult {
    access_token: string;
    token_type: string;
    user: User;
}

export async function login(email: string, password: string): Promise<LoginResult> {
    const form = new URLSearchParams();
    form.set("username", email); // OAuth2PasswordRequestForm ở backend dùng field "username"
    form.set("password", password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
    });

    if (!response.ok) {
        const body = await response.text();
        throw new Error(`API error ${response.status}: ${body}`);
    }
    return response.json();
}

export function fetchCurrentUser(): Promise<User> {
    return apiFetch<User>("/auth/me");
}