from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.system import (
    router as system_router,
)
from backend.app.api.agent import (
    router as agent_router,
)
from backend.app.api.multi_agent import (
    router as multi_agent_router,
)
from backend.app.api.auth import (
    router as auth_router,
)
from backend.app.api.inspection_vision import (
    router as inspection_vision_router,
)
from backend.app.multi_agent.web_search import (
    close_web_search_client,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """统一释放应用运行期间建立的外部连接。"""

    try:
        yield
    finally:
        close_web_search_client()

app = FastAPI(
    title="医院物业安管系统 API",
    description="医院物业安管系统后端接口",
    version="0.2.0",
    lifespan=lifespan,
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
app.include_router(multi_agent_router)
app.include_router(auth_router)
app.include_router(inspection_vision_router)

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
