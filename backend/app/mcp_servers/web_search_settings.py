import os
from pathlib import Path

from dotenv import load_dotenv

from backend.app.core.setting_validation import (
    get_required_env_setting,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


TAVILY_API_KEY = get_required_env_setting(
    "TAVILY_API_KEY",
    ENV_FILE,
)


try:
    WEB_SEARCH_MAX_RESULTS = int(
        os.getenv("WEB_SEARCH_MAX_RESULTS", "5")
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
