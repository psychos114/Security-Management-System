from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.system import (
    router as system_router,
)
from backend.app.api.agent import (
    router as agent_router,
)

app = FastAPI(
    title="医院物业安管系统 API",
    description="医院物业安管系统后端接口",
    version="0.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


# 注册系统概览接口
app.include_router(system_router)
app.include_router(agent_router)

@app.get(
    "/api/health",
    tags=["系统"],
    summary="检查后端运行状态",
)
def health_check():
    return {
        "status": "ok",
        "service": "security-management-backend",
        "message": "安管系统后端运行正常",
    }