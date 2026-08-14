import json
from typing import Any

from backend.app.db.connection import (
    get_read_connection,
)


USER_SELECT = """
SELECT
    u.id,
    u.username,
    u.display_name,
    u.is_active,
    u.is_demo,
    r.code AS role_code,
    r.name AS role_name,
    r.permissions_json
FROM users AS u
JOIN roles AS r
    ON r.id = u.role_id
"""


def row_to_user(
    row,
) -> dict[str, Any]:
    """把数据库记录整理成用户信息。"""

    permissions = json.loads(
        row["permissions_json"]
    )

    if not isinstance(permissions, list):
        permissions = []

    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "display_name": str(
            row["display_name"]
        ),
        "role_code": str(
            row["role_code"]
        ),
        "role_name": str(
            row["role_name"]
        ),
        "permissions": [
            str(permission)
            for permission in permissions
        ],
        "is_active": bool(
            row["is_active"]
        ),
        "is_demo": bool(
            row["is_demo"]
        ),
    }


def get_user_by_username(
    username: str,
) -> dict[str, Any] | None:
    """按照用户名读取用户和角色。"""

    connection = get_read_connection()

    try:
        row = connection.execute(
            USER_SELECT
            + """
            WHERE u.username = ?
            LIMIT 1
            """,
            (username,),
        ).fetchone()

        if row is None:
            return None

        return row_to_user(row)

    finally:
        connection.close()


def get_user_by_id(
    user_id: int,
) -> dict[str, Any] | None:
    """按照用户编号读取用户和角色。"""

    connection = get_read_connection()

    try:
        row = connection.execute(
            USER_SELECT
            + """
            WHERE u.id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        return row_to_user(row)

    finally:
        connection.close()