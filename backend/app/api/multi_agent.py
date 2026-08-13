import logging
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from langgraph.types import Command

from backend.app.multi_agent.hitl_graph import (
    security_agent_hitl_graph,
)
from backend.app.multi_agent.state import (
    create_initial_state,
)
from backend.app.schemas.multi_agent import (
    HumanConfirmationRequest,
    MultiAgentQueryRequest,
    MultiAgentResponse,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/multi-agent",
    tags=["LangGraph多Agent"],
)


def build_graph_config(
    request_id: str,
) -> dict[str, Any]:
    """使用请求编号建立LangGraph会话配置。"""

    return {
        "configurable": {
            "thread_id": request_id,
        }
    }


def build_api_response(
    state: dict[str, Any],
) -> dict[str, Any]:
    """把LangGraph状态整理成前端需要的数据。"""

    confirmation_status = state.get(
        "confirmation_status",
        "not_required",
    )

    interrupts = state.get(
        "__interrupt__",
        [],
    )

    if (
        confirmation_status == "pending"
        or bool(interrupts)
    ):
        run_status = "awaiting_confirmation"
    elif confirmation_status == "approved":
        run_status = "approved"
    elif confirmation_status == "rejected":
        run_status = "rejected"
    else:
        run_status = "completed"

    return {
        "request_id": state["request_id"],
        "run_status": run_status,
        "category": state["category"],
        "risk_level": state["risk_level"],
        "answer_status": state["answer_status"],
        "answer_validation_passed": state[
            "answer_validation_passed"
        ],
        "answer": state["final_answer"],
        "used_doc_codes": state[
            "used_doc_codes"
        ],
        "citations": state["citations"],
        "requires_human_confirmation": state[
            "requires_human_confirmation"
        ],
        "confirmation_status": (
            confirmation_status
        ),
        "confirmed_by": state.get(
            "confirmed_by",
            "",
        ),
        "pending_action": state.get(
            "pending_action"
        ),
        "route_history": state[
            "route_history"
        ],
    }


@router.post(
    "/query",
    response_model=MultiAgentResponse,
    summary="向LangGraph多Agent系统提问",
)
def query_multi_agent(
    request: MultiAgentQueryRequest,
):
    """运行多Agent流程，必要时暂停等待确认。"""

    try:
        initial_state = create_initial_state(
            request.question
        )

        request_id = initial_state[
            "request_id"
        ]

        config = build_graph_config(
            request_id
        )

        result = (
            security_agent_hitl_graph.invoke(
                initial_state,
                config=config,
            )
        )

        return build_api_response(result)

    except Exception as error:
        logger.exception(
            "多Agent问题处理失败"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "多Agent问题处理失败，"
                    "请查看后端控制台"
                ),
                "error_type": (
                    type(error).__name__
                ),
            },
        ) from error


@router.post(
    "/confirm",
    response_model=MultiAgentResponse,
    summary="批准或拒绝待确认动作",
)
def confirm_multi_agent_action(
    request: HumanConfirmationRequest,
):
    """恢复之前暂停的LangGraph流程。"""

    request_id = str(request.request_id)

    config = build_graph_config(
        request_id
    )

    try:
        snapshot = (
            security_agent_hitl_graph.get_state(
                config
            )
        )

        state = snapshot.values

        if not state:
            raise HTTPException(
                status_code=404,
                detail="没有找到对应的待确认任务",
            )

        if (
            state.get("confirmation_status")
            != "pending"
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "该任务当前不处于待确认状态，"
                    "不能重复确认"
                ),
            )

        if (
            "human_confirmation"
            not in snapshot.next
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "该任务没有暂停在人工确认节点"
                ),
            )

        result = (
            security_agent_hitl_graph.invoke(
                Command(
                    resume={
                        "approved": (
                            request.approved
                        ),
                        "operator": (
                            request.operator
                        ),
                        "note": request.note,
                    }
                ),
                config=config,
            )
        )

        return build_api_response(result)

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "人工确认处理失败"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "人工确认处理失败，"
                    "请查看后端控制台"
                ),
                "error_type": (
                    type(error).__name__
                ),
            },
        ) from error