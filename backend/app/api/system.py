from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from backend.app.core.security import (
    get_current_user,
    require_permission,
)
from backend.app.schemas.auth import (
    AuthenticatedUser,
)
from backend.app.services.system_service import (
    get_system_overview,
)


router = APIRouter(
    prefix="/api/system",
    tags=["系统"],
)


@router.get(
    "/overview",
    summary="获取系统概览",
)
def system_overview(
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    """
    返回数据库连接状态和业务数据统计。
    """

    require_permission(
        user=current_user,
        permission="dashboard:view_all",
    )

    try:
        return get_system_overview()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"读取系统概览失败：{error}",
        ) from error