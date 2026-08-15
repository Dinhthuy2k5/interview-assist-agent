export type UserRole = "hr_admin" | "interviewer" | "council";

export interface User {
    id: string;
    email: string;
    full_name: string;
    role: UserRole;
    is_active: boolean;
}

export const ROLE_LABEL: Record<UserRole, string> = {
    hr_admin: "HR Admin",
    interviewer: "Interviewer",
    council: "Hội đồng tuyển dụng",
};