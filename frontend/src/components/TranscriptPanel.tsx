import { useEffect, useState } from "react";
import { getTranscript, uploadTranscriptAudio } from "../api/transcripts";
import type { Transcript } from "../types/transcript";

interface Props {
    sessionId: string;
}

const STATUS_LABEL: Record<string, string> = {
    pending: "Đang chờ xử lý",
    processing: "Đang xử lý",
    completed: "Đã xử lý xong",
    failed: "Xử lý thất bại",
};

function formatExpiryDate(iso: string): string {
    return new Date(iso).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export default function TranscriptPanel({ sessionId }: Props) {
    const [transcript, setTranscript] = useState<Transcript | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [showText, setShowText] = useState(false);

    function load() {
        setLoading(true);
        setLoadError(null);
        setShowText(false); // tránh transcript session trước tự lộ ra khi chuyển session
        getTranscript(sessionId)
            .then(setTranscript)
            .catch(() => setLoadError("Không tải được trạng thái transcript."))
            .finally(() => setLoading(false));
    }

    useEffect(load, [sessionId]);

    async function handleUpload(e: React.FormEvent) {
        e.preventDefault();
        if (!file) return;
        setUploading(true);
        setUploadError(null);
        try {
            const result = await uploadTranscriptAudio(sessionId, file);
            setTranscript(result);
            setFile(null);
        } catch (err) {
            setUploadError(err instanceof Error ? err.message : "Tải lên thất bại, thử lại.");
        } finally {
            setUploading(false);
        }
    }

    if (loading) {
        return (
            <div className="transcript-panel">
                <p className="field-hint" style={{ margin: 0 }}>
                    Đang tải trạng thái bản ghi âm...
                </p>
            </div>
        );
    }

    // Cho phép upload khi: chưa có transcript nào, HOẶC bản ghi trước đó failed
    // (retry) - backend giờ chấp nhận ghi đè trong 2 trường hợp này.
    const canUpload = !transcript || transcript.status === "failed";

    return (
        <div className="transcript-panel">
            <p className="transcript-panel-title">Bản ghi âm &amp; transcript</p>

            {loadError && <div className="notice notice-error">{loadError}</div>}

            {transcript?.status === "failed" && (
                <div className="notice notice-error">
                    Xử lý audio thất bại lần trước - tải lên bản ghi khác bên dưới để thử lại.
                </div>
            )}

            {canUpload ? (
                <form onSubmit={handleUpload} className="transcript-upload-form">
                    <input
                        type="file"
                        accept="audio/*"
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                        disabled={uploading}
                    />
                    <button className="btn btn-secondary" type="submit" disabled={!file || uploading}>
                        {uploading
                            ? "Đang xử lý audio (có thể mất vài phút)..."
                            : transcript
                                ? "Tải lại & xử lý"
                                : "Tải lên & xử lý"}
                    </button>
                    {uploadError && (
                        <div
                            className="notice notice-error"
                            style={{ marginTop: "0.6rem", marginBottom: 0, width: "100%" }}
                        >
                            {uploadError}
                        </div>
                    )}
                </form>
            ) : (
                <div>
                    <div className="transcript-status-row">
                        <span className={`status-badge ${transcript.status === "completed" ? "parsed" : "pending"}`}>
                            {STATUS_LABEL[transcript.status]}
                        </span>
                        {transcript.status === "completed" && (
                            <button type="button" className="btn-icon-toggle" onClick={() => setShowText((v) => !v)}>
                                {showText ? "Ẩn transcript" : "Xem transcript"}
                            </button>
                        )}
                    </div>

                    {showText && transcript.status === "completed" && (
                        <div className="transcript-text-box">{transcript.text}</div>
                    )}

                    <p className="field-hint" style={{ marginTop: "0.6rem", marginBottom: 0 }}>
                        Bản ghi âm sẽ tự động hết hạn vào {formatExpiryDate(transcript.retention_expiry)}.
                    </p>
                </div>
            )}
        </div>
    );
}