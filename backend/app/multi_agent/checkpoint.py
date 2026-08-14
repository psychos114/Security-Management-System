import sqlite3
from pathlib import Path

from backend.app.core.config import (
    CHECKPOINT_DATABASE_PATH,
)

# 必须在读取.env之后导入。
from langgraph.checkpoint.sqlite import (
    SqliteSaver,
)


def create_sqlite_checkpointer(
    database_path: Path = (
        CHECKPOINT_DATABASE_PATH
    ),
):
    """创建可以跨进程重启保存状态的检查点。"""

    resolved_path = Path(
        database_path
    ).resolve()

    resolved_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        str(resolved_path),
        check_same_thread=False,
    )

    # 等待数据库锁最多5秒，避免短暂并发直接报错。
    connection.execute(
        "PRAGMA busy_timeout = 5000"
    )

    # 提高本地开发时的读写兼容性。
    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    checkpointer = SqliteSaver(
        connection
    )

    return checkpointer, connection


sqlite_checkpointer, checkpoint_connection = (
    create_sqlite_checkpointer()
)