from backend.app.core.config import DATABASE_PATH
from backend.app.db.connection import get_read_connection


def get_table_count(connection, table_name):
    """
    查询指定数据表的记录数量。

    table_name只允许由后端代码传入，
    不接收用户输入。
    """
    allowed_tables = {
        "users",
        "event_types",
        "incident_examples",
        "inspection_items",
        "complaints",
        "risk_points",
        "knowledge_documents",
        "knowledge_sources",
        "daily_report_samples",
    }

    if table_name not in allowed_tables:
        raise ValueError(
            f"不允许查询数据表：{table_name}"
        )

    row = connection.execute(
        f"SELECT COUNT(*) AS total "
        f"FROM {table_name}"
    ).fetchone()

    return row["total"]


def get_system_overview():
    """
    读取系统概览统计。
    """
    connection = get_read_connection()

    try:
        integrity_result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        counts = {
            "users": get_table_count(
                connection,
                "users",
            ),
            "event_types": get_table_count(
                connection,
                "event_types",
            ),
            "incident_examples": get_table_count(
                connection,
                "incident_examples",
            ),
            "inspection_items": get_table_count(
                connection,
                "inspection_items",
            ),
            "complaints": get_table_count(
                connection,
                "complaints",
            ),
            "risk_points": get_table_count(
                connection,
                "risk_points",
            ),
            "knowledge_documents": get_table_count(
                connection,
                "knowledge_documents",
            ),
            "knowledge_sources": get_table_count(
                connection,
                "knowledge_sources",
            ),
            "daily_reports": get_table_count(
                connection,
                "daily_report_samples",
            ),
        }

        return {
            "status": "ok",
            "database": {
                "connected": True,
                "integrity": integrity_result,
                "filename": DATABASE_PATH.name,
            },
            "counts": counts,
        }
    finally:
        connection.close()