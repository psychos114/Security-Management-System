import sqlite3

from backend.app.core.config import DATABASE_PATH


def get_read_connection():
    """
    创建只读用途的SQLite连接。

    当前连接只能查询，不能修改数据库。
    """
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"找不到SQLite数据库：{DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        str(DATABASE_PATH)
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")

    return connection