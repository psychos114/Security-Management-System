import logging
from functools import lru_cache

from fastapi import APIRouter
from fastapi import HTTPException

from backend.app.agentic_rag.agent import (
    AgenticRAGService,
)
from backend.app.agentic_rag.tools import (
    RAG_TOOL_DEFINITIONS,
)
from backend.app.core.config import (
    LLM_MODEL,
)
from backend.app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentStatusResponse,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/agent",
    tags=["Agentic RAG"],
)


@lru_cache(maxsize=1)
def get_agent_service():
    """
    整个后端只加载一份FAISS索引和Agent服务。

    每个用户请求中的消息和工具状态仍然相互独立。
    """
    return AgenticRAGService()


@router.get(
    "/status",
    response_model=AgentStatusResponse,
    summary="检查Agentic RAG服务状态",
)
def get_agent_status():
    """
    检查工具、模型配置和FAISS索引是否能够加载。

    该接口不会向AI发送问题。
    """
    try:
        service = get_agent_service()

        vector_count = (
            service
            .tool_executor
            .semantic_retriever
            .index
            .ntotal
        )

        tool_names = [
            item["function"]["name"]
            for item in RAG_TOOL_DEFINITIONS
        ]

        return {
            "status": "ok",
            "service": "agentic-rag",
            "model": LLM_MODEL,
            "vector_count": vector_count,
            "tools": tool_names,
        }

    except Exception as error:
        logger.exception(
            "Agentic RAG状态检查失败"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "Agentic RAG服务暂时不可用"
                ),
                "error_type": (
                    type(error).__name__
                ),
            },
        ) from error


@router.post(
    "/query",
    response_model=AgentQueryResponse,
    summary="向Agentic RAG提问",
)
def query_agent(
    request: AgentQueryRequest,
):
    """
    执行一次独立的Agentic RAG问答。

    Agent会自主检索知识库、打开完整资料，
    然后生成带引用的回答。
    """
    try:
        service = get_agent_service()

        return service.ask(
            request.question
        )

    except Exception as error:
        logger.exception(
            "Agentic RAG问题处理失败"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "Agent处理问题失败，"
                    "请检查后端控制台日志"
                ),
                "error_type": (
                    type(error).__name__
                ),
            },
        ) from error