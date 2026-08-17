import logging
import json
import time
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from typing import Annotated

from fastapi import Depends

from backend.app.core.security import (
    get_current_user,
    require_task_confirmation,
)
from backend.app.schemas.auth import (
    AuthenticatedUser,
)

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


STREAM_CHUNK_SIZE = 12
STREAM_CHUNK_DELAY_SECONDS = 0.012


STREAM_NODE_MESSAGES = {
    "supervisor": "正在判断问题类型和风险等级",
    "emergency_agent": "突发事件Agent正在制定检索计划",
    "inspection_agent": "巡检Agent正在制定检索计划",
    "complaint_report_agent": (
        "投诉与日报Agent正在制定检索计划"
    ),
    "fire_compliance_agent": (
        "消防法规Agent正在制定检索计划"
    ),
    "controlled_retrieval": (
        "正在执行受控混合检索"
    ),
    "open_evidence_documents": (
        "正在打开白名单内的完整资料"
    ),
    "emergency_answer": "正在生成突发事件处置建议",
    "inspection_answer": "正在生成巡检整改建议",
    "complaint_report_answer": (
        "正在生成投诉或日报建议"
    ),
    "fire_compliance_answer": (
        "正在生成消防法规回答"
    ),
    "answer_pipeline": (
        "专业Agent回答已经完成安全检查"
    ),
    "prepare_action": "正在检查是否需要人工确认",
    "human_confirmation": "关键动作正在等待人工确认",
}


def encode_stream_event(
    event_type: str,
    data: dict[str, Any],
) -> str:
    """把一个流事件编码为一行NDJSON。"""

    return (
        json.dumps(
            {
                "type": event_type,
                "data": data,
            },
            ensure_ascii=False,
        )
        + "\n"
    )


def get_stream_node_name(
    update: object,
) -> str:
    """从LangGraph流更新中读取节点名称。"""

    update_data = update

    if (
        isinstance(update, tuple)
        and len(update) == 2
    ):
        update_data = update[1]

    if not isinstance(update_data, dict):
        return ""

    for node_name in update_data:
        if isinstance(node_name, str):
            return node_name

    return ""


def split_answer_chunks(
    answer: str,
) -> Iterator[str]:
    """把已通过安全检查的回答切成流式片段。"""

    for start in range(
        0,
        len(answer),
        STREAM_CHUNK_SIZE,
    ):
        yield answer[
            start:start + STREAM_CHUNK_SIZE
        ]


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
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    """运行多Agent流程，必要时暂停等待确认。"""

    try:
        initial_state = create_initial_state(
            request.question,
            initiator_user_id=current_user.id,
            initiator_role_code=(
                current_user.role_code
            ),
            initiator_display_name=(
                current_user.display_name
            ),
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
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
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
                    "当前任务已经处理，不能重复确认"
                ),
            )
            
        require_task_confirmation(
            user=current_user,
            task_state=dict(state),
        )

        result = (
            security_agent_hitl_graph.invoke(
                Command(
                    resume={
                        "approved": (
                            request.approved
                        ),
                        "operator": (
                            current_user.display_name
                        ),
                        "operator_user_id": (
                            current_user.id
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


def stream_multi_agent_events(
    request: MultiAgentQueryRequest,
    current_user: AuthenticatedUser,
) -> Iterator[str]:
    """逐步推送多Agent进度和安全回答。"""

    initial_state = create_initial_state(
        request.question,
        initiator_user_id=current_user.id,
        initiator_role_code=(
            current_user.role_code
        ),
        initiator_display_name=(
            current_user.display_name
        ),
    )

    request_id = initial_state[
        "request_id"
    ]

    config = build_graph_config(
        request_id
    )

    yield encode_stream_event(
        "start",
        {
            "request_id": request_id,
            "message": "多Agent已经收到问题",
        },
    )

    last_node_name = ""

    try:
        for update in (
            security_agent_hitl_graph.stream(
                initial_state,
                config=config,
                stream_mode="updates",
                subgraphs=True,
            )
        ):
            node_name = get_stream_node_name(
                update
            )

            if (
                not node_name
                or node_name == last_node_name
            ):
                continue

            last_node_name = node_name

            progress_message = (
                STREAM_NODE_MESSAGES.get(
                    node_name
                )
            )

            if progress_message:
                yield encode_stream_event(
                    "status",
                    {
                        "node": node_name,
                        "message": progress_message,
                    },
                )

        snapshot = (
            security_agent_hitl_graph.get_state(
                config
            )
        )

        result = build_api_response(
            dict(snapshot.values)
        )

        answer = str(
            result.get("answer", "")
        )

        metadata = {
            key: value
            for key, value in result.items()
            if key != "answer"
        }

        yield encode_stream_event(
            "metadata",
            metadata,
        )

        for chunk in split_answer_chunks(
            answer
        ):
            yield encode_stream_event(
                "answer_delta",
                {
                    "text": chunk,
                },
            )

            if STREAM_CHUNK_DELAY_SECONDS:
                time.sleep(
                    STREAM_CHUNK_DELAY_SECONDS
                )

        yield encode_stream_event(
            "complete",
            {
                "result": result,
            },
        )

    except Exception as error:
        logger.exception(
            "多Agent流式问题处理失败"
        )

        yield encode_stream_event(
            "error",
            {
                "message": (
                    "多Agent流式问题处理失败，"
                    "请查看后端控制台"
                ),
                "error_type": (
                    type(error).__name__
                ),
            },
        )


@router.post(
    "/query/stream",
    summary="流式调用LangGraph多Agent系统",
    response_class=StreamingResponse,
)
def stream_query_multi_agent(
    request: MultiAgentQueryRequest,
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    """使用NDJSON持续返回处理进度和正式回答。"""

    return StreamingResponse(
        stream_multi_agent_events(
            request,
            current_user,
        ),
        media_type=(
            "application/x-ndjson; charset=utf-8"
        ),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
