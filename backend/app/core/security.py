from datetime import datetime
from datetime import timedelta
from datetime import timezone
from secrets import compare_digest
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
)
from fastapi.security import HTTPBearer
from jwt.exceptions import InvalidTokenError

from backend.app.core.config import (
    DEMO_AUTH_PASSWORD,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from backend.app.db.auth_repository import (
    get_user_by_id,
)
from backend.app.schemas.auth import (
    AuthenticatedUser,
)


bearer_scheme = HTTPBearer()


def build_authenticated_user(
    user_record: dict,
) -> AuthenticatedUser:
    """把数据库记录转换为认证用户。"""

    return AuthenticatedUser(
        id=user_record["id"],
        username=user_record["username"],
        display_name=(
            user_record["display_name"]
        ),
        role_code=user_record["role_code"],
        role_name=user_record["role_name"],
        permissions=user_record[
            "permissions"
        ],
        is_demo=user_record["is_demo"],
    )


def verify_demo_password(
    provided_password: str,
) -> bool:
    """检查学习项目统一演示密码。"""

    return compare_digest(
        provided_password,
        DEMO_AUTH_PASSWORD,
    )


def create_access_token(
    user: AuthenticatedUser,
) -> str:
    """为已认证用户签发短期JWT。"""

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=(
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user.id),
        "username": user.username,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def credentials_exception():
    """建立统一的未认证错误。"""

    return HTTPException(
        status_code=401,
        detail="登录状态无效或已经过期",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> AuthenticatedUser:
    """从Bearer令牌读取当前用户。"""

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")

        if (
            not isinstance(subject, str)
            or not subject.isdigit()
        ):
            raise credentials_exception()

    except InvalidTokenError as error:
        raise credentials_exception() from error

    user_record = get_user_by_id(
        int(subject)
    )

    if (
        user_record is None
        or not user_record["is_active"]
    ):
        raise credentials_exception()

    return build_authenticated_user(
        user_record
    )


def require_incident_confirmation(
    user: AuthenticatedUser,
    risk_level: str,
) -> None:
    """检查当前角色能否确认关键事件。"""

    user_permissions = set(
        user.permissions
    )

    if risk_level == "critical":
        allowed_permissions = {
            "incident:approve_critical",
            "incident:approve_major",
        }
    else:
        allowed_permissions = {
            "incident:confirm",
            "incident:approve_critical",
            "incident:approve_major",
        }

    if user_permissions.isdisjoint(
        allowed_permissions
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                f"当前角色“{user.role_name}”"
                "没有确认该事件的权限"
            ),
        )