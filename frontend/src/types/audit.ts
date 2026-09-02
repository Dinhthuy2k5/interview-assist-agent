export interface AuditLogEntry {
    id: string;
    actor_id: string | null;
    actor_name: string | null;
    action: string;
    target_type: string | null;
    target_id: string | null;
    detail: string | null;
    created_at: string;
}