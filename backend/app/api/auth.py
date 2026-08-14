from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from backend.app.core.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
)
from backend.app.core.security import (
    build_authenticated_user,
    create_access_token,
    get_current_user,
    verify_demo_password,
)
from backend.app.db.auth_repository import (
    get_user_by_username,
)
from backend.app.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    LoginResponse,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["身份认证"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="演示用户登录",
)
def login(
    request: LoginRequest,
):
    """验证演示用户并签发JWT。"""

    user_record = get_user_by_username(
        request.username
    )

    provided_password = (
        request.password.get_secret_value()
    )

    password_valid = (
        verify_demo_password(
            provided_password
        )
    )

    if (
        user_record is None
        or not password_valid
        or not user_record["is_active"]
    ):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    user = build_authenticated_user(
        user_record
    )

    access_token = create_access_token(
        user
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            * 60
        ),
        "user": user,
    }


@router.get(
    "/me",
    response_model=AuthenticatedUser,
    summary="读取当前登录用户",
)
def get_me(
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    return current_user