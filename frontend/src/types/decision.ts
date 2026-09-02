export type DecisionValue = "hired" | "rejected" | "on_hold";

export interface Decision {
    id: string;
    session_id: string;
    decided_by: string;
    decided_by_name: string;
    decision: DecisionValue;
    rationale: string;
    created_at: string;
}