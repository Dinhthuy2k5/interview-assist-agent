import type { JdParseStatus } from "../types/job";

interface Props {
    status: JdParseStatus | "idle";
}

const STEPS = [
    { key: "upload", label: "Tải lên" },
    { key: "extract", label: "Trích xuất" },
    { key: "confirm", label: "Xác nhận" },
] as const;

function stepState(stepKey: (typeof STEPS)[number]["key"], status: Props["status"]) {
    if (status === "idle") return stepKey === "upload" ? "active" : "pending";
    if (stepKey === "upload") return "done";
    if (stepKey === "extract") return "done";
    if (stepKey === "confirm") {
        return status === "needs_review" ? "active" : "done";
    }
    return "pending";
}

export default function PipelineStepper({ status }: Props) {
    return (
        <div className="pipeline">
            {STEPS.map((step, i) => {
                const state = stepState(step.key, status);
                return (
                    <div key={step.key} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div className={`pipeline-step ${state === "done" ? "is-done" : ""} ${state === "active" ? "is-active" : ""}`}>
                            <span className="pipeline-dot" />
                            <span>{step.label}</span>
                        </div>
                        {i < STEPS.length - 1 && <div className="pipeline-line" />}
                    </div>
                );
            })}
        </div>
    );
}