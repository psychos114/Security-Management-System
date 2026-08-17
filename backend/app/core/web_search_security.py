import ipaddress
from urllib.parse import urlparse


def normalize_domain(value: str) -> str:
    """把配置或工具参数中的域名整理成统一格式。"""

    domain = str(value).strip().lower().rstrip(".")

    if not domain:
        raise ValueError("搜索域名不能为空")

    if (
        "://" in domain
        or "/" in domain
        or "@" in domain
        or ":" in domain
    ):
        raise ValueError(
            "搜索域名只能填写纯域名"
        )

    return domain.lstrip(".")


def domain_is_allowed(
    hostname: str,
    allowed_domains: tuple[str, ...],
) -> bool:
    """只允许白名单域名及其子域名。"""

    normalized_host = str(
        hostname
    ).strip().lower().rstrip(".")

    for allowed_domain in allowed_domains:
        normalized_allowed = normalize_domain(
            allowed_domain
        )

        if (
            normalized_host == normalized_allowed
            or normalized_host.endswith(
                "." + normalized_allowed
            )
        ):
            return True

    return False


def validate_search_result_url(
    value: str,
    allowed_domains: tuple[str, ...],
) -> tuple[str, str]:
    """阻止私网、IP、非HTTPS和白名单外的搜索结果。"""

    url = str(value).strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() != "https":
        raise ValueError(
            "搜索结果必须使用HTTPS"
        )

    if parsed.username or parsed.password:
        raise ValueError(
            "搜索结果URL不能包含登录信息"
        )

    if parsed.port not in {None, 443}:
        raise ValueError(
            "搜索结果URL不能使用自定义端口"
        )

    hostname = str(
        parsed.hostname or ""
    ).strip().lower().rstrip(".")

    if not hostname:
        raise ValueError(
            "搜索结果URL缺少域名"
        )

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError(
            "搜索结果URL不能直接使用IP地址"
        )

    if not domain_is_allowed(
        hostname,
        allowed_domains,
    ):
        raise PermissionError(
            "搜索结果域名不在白名单内"
        )

    return url, hostname
