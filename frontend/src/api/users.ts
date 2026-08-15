import { apiFetch } from "./client";
import type { User, UserRole } from "../types/user";

export interface CreateUserPayload {
    email: string;
    full_name: string;
    password: string;
    role: UserRole;
}

export function createUser(payload: CreateUserPayload): Promise<User> {
    return apiFetch<User>("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}

export function listUsers(): Promise<User[]> {
    return apiFetch<User[]>("/users");
}