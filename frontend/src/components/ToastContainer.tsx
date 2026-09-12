import { useToast, type ToastType } from "../contexts/ToastContext";

function getToastIcon(type: ToastType): string {
    switch (type) {
        case "success":
            return "✓";
        case "error":
            return "✕";
        case "warning":
            return "⚠";
        case "info":
        default:
            return "ℹ";
    }
}

export default function ToastContainer() {
    const { toasts, dismiss } = useToast();

    if (toasts.length === 0) {
        return null;
    }

    return (
        <aside className="toast-container" aria-live="polite" aria-label="Thông báo hệ thống">
            {toasts.map((t) => (
                <div key={t.id} className={`toast-item toast-${t.type}`} role="status">
                    <span className="toast-icon">{getToastIcon(t.type)}</span>
                    <p className="toast-message">{t.message}</p>
                    <button
                        type="button"
                        className="toast-close-btn"
                        onClick={() => dismiss(t.id)}
                        aria-label="Đóng thông báo"
                    >
                        &times;
                    </button>
                </div>
            ))}
        </aside>
    );
}
