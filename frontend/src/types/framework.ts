export interface Criterion {
    id: string;
    name: string;
    weight: number;
    scoring_rubric: string;
}

export interface CompetencyFramework {
    id: string;
    name: string;
    description: string | null;
    criteria: Criterion[];
}