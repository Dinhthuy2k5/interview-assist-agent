from fastapi import FastAPI

app = FastAPI(
    title="Interview Assist Agent API",
    description="AI Agent hỗ trợ phỏng vấn & tổng hợp đánh giá ứng viên (đề tài 113 / BO-17)",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Dùng cho docker healthcheck và verify service sống."""
    return {"status": "ok", "service": "interview-assist-agent-backend"}