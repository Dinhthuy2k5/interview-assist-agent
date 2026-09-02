import { apiFetch } from "./client";
import type { AuditLogEntry } from "../types/audit";

export function listAuditLog(limit = 100): Promise<AuditLogEntry[]> {
    return apiFetch<AuditLogEntry[]>(`/audit-log?limit=${limit}`);
}