import os
from pathlib import Path

from dotenv import load_dotenv


# D:\Desktop\Security_Management_System
PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


def get_required_setting(name):
    """
    读取必须存在的配置，但不打印密钥。
    """
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"缺少配置项{name}，请检查：{ENV_FILE}"
        )

    if "这里换成" in value:
        raise RuntimeError(
            f"配置项{name}仍然是演示文字"
        )

    return value


def resolve_project_path(value):
    """
    将相对路径转换成项目内的完整路径。
    """
    path = Path(value)

    if path.is_absolute():
        return path

    return (PROJECT_ROOT / path).resolve()


DATABASE_PATH = resolve_project_path(
    os.getenv(
        "DATABASE_PATH",
        "database/security_management_demo.db",
    )
)

VECTOR_INDEX_PATH = resolve_project_path(
    os.getenv(
        "VECTOR_INDEX_PATH",
        "database/vector_index/security_knowledge",
    )
)

EMBEDDING_BASE_URL = get_required_setting(
    "EMBEDDING_BASE_URL"
)

EMBEDDING_API_KEY = get_required_setting(
    "EMBEDDING_API_KEY"
)

EMBEDDING_MODEL = get_required_setting(
    "EMBEDDING_MODEL"
)


try:
    EMBEDDING_BATCH_SIZE = int(
        os.getenv("EMBEDDING_BATCH_SIZE", "10")
    )
except ValueError as error:
    raise RuntimeError(
        "EMBEDDING_BATCH_SIZE必须是整数"
    ) from error


if EMBEDDING_BATCH_SIZE < 1:
    raise RuntimeError(
        "EMBEDDING_BATCH_SIZE不能小于1"
    )


LLM_BASE_URL = get_required_setting(
    "LLM_BASE_URL"
)

LLM_API_KEY = get_required_setting(
    "LLM_API_KEY"
)

LLM_MODEL = get_required_setting(
    "LLM_MODEL"
)


try:
    LLM_MAX_ROUNDS = int(
        os.getenv(
            "LLM_MAX_ROUNDS",
            "6",
        )
    )
except ValueError as error:
    raise RuntimeError(
        "LLM_MAX_ROUNDS必须是整数"
    ) from error


try:
    LLM_MAX_TOOL_CALLS = int(
        os.getenv(
            "LLM_MAX_TOOL_CALLS",
            "10",
        )
    )
except ValueError as error:
    raise RuntimeError(
        "LLM_MAX_TOOL_CALLS必须是整数"
    ) from error


if not 2 <= LLM_MAX_ROUNDS <= 10:
    raise RuntimeError(
        "LLM_MAX_ROUNDS必须在2到10之间"
    )


if not 2 <= LLM_MAX_TOOL_CALLS <= 20:
    raise RuntimeError(
        "LLM_MAX_TOOL_CALLS必须在2到20之间"
    )