from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.competency import router as competency_router
from app.api.jobs import router as jobs_router
from app.api.questions import router as questions_router
from app.api.users import router as users_router

app = FastAPI(
    title="Interview Assist Agent API",
    description="AI Agent hỗ trợ phỏng vấn & tổng hợp đánh giá ứng viên (đề tài 113 / BO-17)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competency_router)
app.include_router(jobs_router)
app.include_router(questions_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "interview-assist-agent-backend"}