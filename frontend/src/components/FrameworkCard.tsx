import { useState } from "react";
import type { CompetencyFramework, Criterion } from "../types/framework";
import { parseRubric } from "../utils/rubric";

function CriterionBlock({ criterion, totalWeight }: { criterion: Criterion; totalWeight: number }) {
    const [expanded, setExpanded] = useState(false);
    const percent = totalWeight > 0 ? Math.round((criterion.weight / totalWeight) * 1000) / 10 : 0;
    const levels = parseRubric(criterion.scoring_rubric);

    return (
        <div className="criterion-block">
            <div className="criterion-block-header">
                <p className="criterion-block-name">{criterion.name}</p>
                <span className="weight-pill">{percent}%</span>
            </div>

            <div className="weight-bar-track">
                <div className="weight-bar-fill" style={{ width: `${percent}%` }} />
            </div>

            <button
                type="button"
                className="rubric-toggle"
                onClick={() => setExpanded((v) => !v)}
                aria-expanded={expanded}
            >
                {expanded ? "Ẩn rubric chấm điểm" : "Xem rubric chấm điểm"}
            </button>

            {expanded && (
                <div className="rubric-table">
                    {levels.map((l, i) => (
                        <div className="rubric-row" key={i}>
                            {l.level && <span className="rubric-level">{l.level}</span>}
                            <span className="rubric-text">{l.text}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default function FrameworkCard({ framework }: { framework: CompetencyFramework }) {
    const totalWeight = framework.criteria.reduce((sum, c) => sum + c.weight, 0);

    return (
        <div className="card framework-card">
            <div className="framework-card-header">
                <div>
                    <h3 className="framework-card-name">{framework.name}</h3>
                    {framework.description && (
                        <p className="framework-card-desc">{framework.description}</p>
                    )}
                </div>
                <span className="criteria-count-pill">{framework.criteria.length} tiêu chí</span>
            </div>

            <div className="criterion-list">
                {framework.criteria.map((c) => (
                    <CriterionBlock key={c.id} criterion={c} totalWeight={totalWeight} />
                ))}
            </div>
        </div>
    );
}