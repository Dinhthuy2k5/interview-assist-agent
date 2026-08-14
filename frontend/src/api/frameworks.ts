import { apiFetch } from "./client";
import type { CompetencyFramework } from "../types/framework";

export function listFrameworks(): Promise<CompetencyFramework[]> {
    return apiFetch<CompetencyFramework[]>("/frameworks");
}