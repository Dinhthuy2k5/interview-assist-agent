import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface ToastItem {
    id: string;
    type: ToastType;
    message: string;
}

interface ToastContextValue {
    toasts: ToastItem[];
    success: (message: string, durationMs?: number) => void;
    error: (message: string, durationMs?: number) => void;
    info: (message: string, durationMs?: number) => void;
    warning: (message: string, durationMs?: number) => void;
    dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const DEFAULT_DURATION_MS = 4000;

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastItem[]>([]);

    const dismiss = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const addToast = useCallback(
        (type: ToastType, message: string, durationMs: number = DEFAULT_DURATION_MS) => {
            const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
            const newToast: ToastItem = { id, type, message };

            setToasts((prev) => [...prev, newToast]);

            if (durationMs > 0) {
                setTimeout(() => {
                    dismiss(id);
                }, durationMs);
            }
        },
        [dismiss]
    );

    const success = useCallback((msg: string, dur?: number) => addToast("success", msg, dur), [addToast]);
    const error = useCallback((msg: string, dur?: number) => addToast("error", msg, dur), [addToast]);
    const info = useCallback((msg: string, dur?: number) => addToast("info", msg, dur), [addToast]);
    const warning = useCallback((msg: string, dur?: number) => addToast("warning", msg, dur), [addToast]);

    return (
        <ToastContext.Provider value={{ toasts, success, error, info, warning, dismiss }}>
            {children}
        </ToastContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastContextValue {
    const ctx = useContext(ToastContext);
    if (!ctx) {
        throw new Error("useToast phải được sử dụng bên trong ToastProvider");
    }
    return ctx;
}
