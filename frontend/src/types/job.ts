export type JdParseStatus = "pending" | "parsed" | "needs_review";
export type JobStatus = "open" | "closed";

export interface Job {
    id: string;
    title: string;
    level: string;
    jd_file_path: string;
    jd_text: string | null;
    jd_parse_status: JdParseStatus;
    framework_id: string;
    created_by: string;
    application_deadline: string | null;
    is_closed: boolean;
    status: JobStatus;
    created_at: string;
    updated_at: string;
}