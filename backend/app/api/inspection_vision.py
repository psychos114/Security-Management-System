import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status
from starlette.concurrency import run_in_threadpool

from backend.app.core.security import (
    get_current_user,
)
from backend.app.schemas.auth import (
    AuthenticatedUser,
)
from backend.app.schemas.inspection_vision import (
    InspectionVisionApiResponse,
    InspectionVisionResult,
)
from backend.app.services.inspection_vision_service import (
    InspectionVisionService,
)
from backend.app.api.multi_agent import (
    build_api_response,
    build_graph_config,
)
from backend.app.multi_agent.hitl_graph import (
    security_agent_hitl_graph,
)
from backend.app.services.inspection_agent_bridge import (
    create_visual_inspection_state,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/inspection-vision",
    tags=["巡检图片分析"],
)

vision_service = InspectionVisionService()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def detect_image_suffix(
    content: bytes,
) -> str:
    """根据文件真实内容判断图片格式。"""

    if content.startswith(
        b"\xff\xd8\xff"
    ):
        return ".jpg"

    if content.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):
        return ".png"

    if (
        len(content) >= 12
        and content[:4] == b"RIFF"
        and content[8:12] == b"WEBP"
    ):
        return ".webp"

    raise HTTPException(
        status_code=(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ),
        detail=(
            "文件内容不是有效的JPG、PNG"
            "或WebP图片"
        ),
    )


def run_visual_inspection_agent(
    analysis_id: str,
    result: InspectionVisionResult,
):
    """把图片结果送进LangGraph巡检流程。"""

    initial_state = (
        create_visual_inspection_state(
            analysis_id=analysis_id,
            result=result,
        )
    )

    config = build_graph_config(
        initial_state["request_id"]
    )

    return (
        security_agent_hitl_graph.invoke(
            initial_state,
            config=config,
        )
    )


@router.post(
    "/analyze",
    response_model=InspectionVisionApiResponse,
    summary="上传并分析巡检照片",
)
async def analyze_inspection_image(
    image: Annotated[
        UploadFile,
        File(
            description="需要分析的巡检照片"
        ),
    ],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    """分析登录用户上传的一张巡检照片。"""

    original_filename = (
        image.filename
        or "uploaded_image"
    )

    safe_filename = Path(
        original_filename
    ).name

    try:
        content = await image.read(
            MAX_UPLOAD_BYTES + 1
        )
    finally:
        await image.close()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="上传的图片内容为空",
        )

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=(
                status.HTTP_413_CONTENT_TOO_LARGE
            ),
            detail="上传图片不能超过10MB",
        )

    suffix = detect_image_suffix(content)

    temporary_path = None

    try:
        with NamedTemporaryFile(
            mode="wb",
            prefix="security_inspection_",
            suffix=suffix,
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)

            temporary_path = Path(
                temporary_file.name
            )

        result = await run_in_threadpool(
            vision_service.analyze,
            temporary_path,
        )

        # 图片识别完成后立即删除临时文件，
        # 后面的LangGraph只使用结构化文字结果。
        temporary_path.unlink(
            missing_ok=True
        )
        temporary_path = None

        analysis_id = uuid4()

        agent_state = await run_in_threadpool(
            run_visual_inspection_agent,
            str(analysis_id),
            result,
        )

        agent_result = build_api_response(
            agent_state
        )

        return {
            "analysis_id": analysis_id,
            "filename": safe_filename,
            "analyzed_by": (
                current_user.display_name
            ),
            "analyzed_by_role": (
                current_user.role_name
            ),
            "result": result,
            "agent_result": agent_result,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "巡检图片与多Agent处理失败"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message": "巡检图片与多Agent处理失败",
                "error_type": (
                    type(error).__name__
                ),
            },
        ) from error

    finally:
        if temporary_path is not None:
            temporary_path.unlink(
                missing_ok=True
            )