import os
from pathlib import Path


PLACEHOLDER_MARKERS = (
    "这里换成",
    "请替换",
    "replace_with",
    "replace-with",
    "your_api_key",
    "your-api-key",
    "your_secret",
    "your-secret",
    "change_me",
    "change-me",
    "changeme",
)


def is_placeholder_setting(value: str) -> bool:
    """识别中英文配置示例中的常见占位文字。"""

    normalized_value = value.strip().lower()

    if not normalized_value:
        return False

    return any(
        marker in normalized_value
        for marker in PLACEHOLDER_MARKERS
    )


def get_required_env_setting(
    name: str,
    env_file: Path,
) -> str:
    """读取必填配置，并阻止空值或示例占位符。"""

    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"缺少配置项{name}，请检查：{env_file}"
        )

    if is_placeholder_setting(value):
        raise RuntimeError(
            f"配置项{name}仍然是演示文字"
        )

    return value
