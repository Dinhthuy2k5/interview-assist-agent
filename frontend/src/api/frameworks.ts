import { apiFetch } from "./client";
import type { CompetencyFramework } from "../types/framework";

export function listFrameworks(): Promise<CompetencyFramework[]> {
    return apiFetch<CompetencyFramework[]>("/frameworks");
}

export interface CreateFrameworkPayload {
    name: string;
    description: string | null;
    criteria: { name: string; weight: number; scoring_rubric: string }[];
}

export function createFramework(payload: CreateFrameworkPayload): Promise<CompetencyFramework> {
    return apiFetch<CompetencyFramework>("/frameworks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}