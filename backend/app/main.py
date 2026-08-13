from fastapi import FastAPI

from app.api.competency import router as competency_router
from app.api.jobs import router as jobs_router

app = FastAPI(
    title="Interview Assist Agent API",
    description="AI Agent hỗ trợ phỏng vấn & tổng hợp đánh giá ứng viên (đề tài 113 / BO-17)",
    version="0.1.0",
)

app.include_router(competency_router)
app.include_router(jobs_router)


@app.get("/health")
def health_check():
    """Dùng cho docker healthcheck và verify service sống."""
    return {"status": "ok", "service": "interview-assist-agent-backend"}