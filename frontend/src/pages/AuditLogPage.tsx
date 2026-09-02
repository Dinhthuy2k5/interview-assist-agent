import { useEffect, useState } from "react";
import { listAuditLog } from "../api/audit";
import type { AuditLogEntry } from "../types/audit";

const ACTION_LABEL: Record<string, string> = {
    login_success: "Đăng nhập thành công",
    login_failed: "Đăng nhập thất bại",
    user_created: "Tạo tài khoản",
    user_updated: "Sửa tài khoản",
    decision_created: "Ghi quyết định",
};

function actionBadgeClass(action: string): string {
    if (action === "login_failed") return "needs_review";
    if (action === "decision_created") return "parsed";
    return "pending";
}

function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString("vi-VN", { dateStyle: "medium", timeStyle: "medium" });
}

export default function AuditLogPage() {
    const [logs, setLogs] = useState<AuditLogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    function load() {
        setLoading(true);
        setLoadError(null);
        listAuditLog()
            .then(setLogs)
            .catch(() => setLoadError("Không tải được nhật ký."))
            .finally(() => setLoading(false));
    }

    useEffect(load, []);

    return (
        <div className="page-content">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
                <div>
                    <h1 className="page-heading">Nhật ký hệ thống</h1>
                    <p className="page-description">
                        Lịch sử đăng nhập, tạo/sửa tài khoản, và quyết định tuyển dụng - 100 hoạt động
                        gần nhất.
                    </p>
                </div>
                <button type="button" className="btn btn-secondary" onClick={load}>
                    Tải lại
                </button>
            </div>

            {loadError && <div className="notice notice-error">{loadError}</div>}
            {loading ? (
                <p className="field-hint">Đang tải...</p>
            ) : logs.length === 0 ? (
                <div className="notice notice-warning">Chưa có hoạt động nào được ghi nhận.</div>
            ) : (
                <div className="card">
                    <table className="user-table">
                        <thead>
                            <tr>
                                <th>Thời gian</th>
                                <th>Người thực hiện</th>
                                <th>Hành động</th>
                                <th>Chi tiết</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log) => (
                                <tr key={log.id}>
                                    <td style={{ whiteSpace: "nowrap" }}>{formatDateTime(log.created_at)}</td>
                                    <td>{log.actor_name ?? "(không xác định)"}</td>
                                    <td>
                                        <span className={`status-badge ${actionBadgeClass(log.action)}`}>
                                            {ACTION_LABEL[log.action] ?? log.action}
                                        </span>
                                    </td>
                                    <td style={{ fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
                                        {log.detail ?? "—"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}