import os
from pathlib import Path

from dotenv import load_dotenv

from backend.app.core.setting_validation import (
    get_required_env_setting,
)


# D:\Desktop\Security_Management_System
PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


def get_required_setting(name):
    """
    读取必须存在的配置，但不打印密钥。
    """
    return get_required_env_setting(
        name,
        ENV_FILE,
    )


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

CHECKPOINT_DATABASE_PATH = (
    resolve_project_path(
        os.getenv(
            "CHECKPOINT_DATABASE_PATH",
            (
                "database/runtime/"
                "langgraph_checkpoints.db"
            ),
        )
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

VISION_BASE_URL = get_required_setting(
    "VISION_BASE_URL"
)

VISION_API_KEY = get_required_setting(
    "VISION_API_KEY"
)

VISION_MODEL = get_required_setting(
    "VISION_MODEL"
)

TAVILY_API_KEY = get_required_setting(
    "TAVILY_API_KEY"
)


def parse_boolean_setting(
    name: str,
    default: str,
) -> bool:
    """读取true/false配置。"""

    value = os.getenv(
        name,
        default,
    ).strip().lower()

    if value in {"1", "true", "yes", "on"}:
        return True

    if value in {"0", "false", "no", "off"}:
        return False

    raise RuntimeError(
        f"{name}必须是true或false"
    )


WEB_SEARCH_ENABLED = parse_boolean_setting(
    "WEB_SEARCH_ENABLED",
    "true",
)


try:
    WEB_SEARCH_MAX_RESULTS = int(
        os.getenv(
            "WEB_SEARCH_MAX_RESULTS",
            "5",
        )
    )
except ValueError as error:
    raise RuntimeError(
        "WEB_SEARCH_MAX_RESULTS必须是整数"
    ) from error


try:
    WEB_SEARCH_TIMEOUT_SECONDS = float(
        os.getenv(
            "WEB_SEARCH_TIMEOUT_SECONDS",
            "15",
        )
    )
except ValueError as error:
    raise RuntimeError(
        "WEB_SEARCH_TIMEOUT_SECONDS必须是数字"
    ) from error


if not 1 <= WEB_SEARCH_MAX_RESULTS <= 5:
    raise RuntimeError(
        "WEB_SEARCH_MAX_RESULTS必须在1到5之间"
    )


if not 3 <= WEB_SEARCH_TIMEOUT_SECONDS <= 30:
    raise RuntimeError(
        "WEB_SEARCH_TIMEOUT_SECONDS必须在3到30秒之间"
    )


WEB_SEARCH_ALLOWED_DOMAINS = tuple(
    domain.strip().lower().lstrip(".")
    for domain in os.getenv(
        "WEB_SEARCH_ALLOWED_DOMAINS",
        (
            "gov.cn,sz.gov.cn,gd.gov.cn,"
            "npc.gov.cn,mem.gov.cn,119.gov.cn"
        ),
    ).split(",")
    if domain.strip()
)


if not WEB_SEARCH_ALLOWED_DOMAINS:
    raise RuntimeError(
        "WEB_SEARCH_ALLOWED_DOMAINS至少需要一个域名"
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


JWT_SECRET_KEY = get_required_setting(
    "JWT_SECRET_KEY"
)

DEMO_AUTH_PASSWORD = get_required_setting(
    "DEMO_AUTH_PASSWORD"
)

JWT_ALGORITHM = "HS256"


try:
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "60",
        )
    )
except ValueError as error:
    raise RuntimeError(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
        "必须是整数"
    ) from error


if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY至少需要32个字符"
    )


if not 5 <= (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES
) <= 1440:
    raise RuntimeError(
        "JWT令牌有效时间必须在"
        "5到1440分钟之间"
    )
