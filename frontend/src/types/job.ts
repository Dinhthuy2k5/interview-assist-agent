export type JdParseStatus = "pending" | "parsed" | "needs_review";

export interface Job {
    id: string;
    title: string;
    level: string;
    jd_file_path: string;
    jd_text: string | null;
    jd_parse_status: JdParseStatus;
    framework_id: string;
    created_by: string;
    created_at: string;
    updated_at: string;
}