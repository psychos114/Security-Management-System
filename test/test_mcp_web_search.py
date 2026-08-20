import _project_path  # noqa: F401

import asyncio

from backend.app.core.config import (
    WEB_SEARCH_ALLOWED_DOMAINS,
)
from backend.app.core.web_search_security import (
    validate_search_result_url,
)
from backend.app.core.setting_validation import (
    is_placeholder_setting,
)
from backend.app.mcp_clients.web_search_client import (
    WebSearchMCPClient,
)
from backend.app.mcp_servers import (
    web_search_server,
)


print("=" * 70)
print("测试1：本地MCP服务可以通过stdio协议启动")

client = WebSearchMCPClient()
health = client.health()

assert health["status"] == "ok"
assert health["provider"] == "tavily"

print("通过：MCP健康工具返回正常")


print("\n" + "=" * 70)
print("测试2：同一客户端复用子进程并支持异步上下文")

worker_thread = client._thread
second_health = client.health()
async_health = asyncio.run(client.ahealth())

assert client._thread is worker_thread
assert second_health["status"] == "ok"
assert async_health["status"] == "ok"

client.close()

print("通过：连续调用没有重启子进程，异步调用正常")


print("\n" + "=" * 70)
print("测试3：搜索工具只保留白名单HTTPS结果")


class FakeTavilyClient:
    def __init__(self):
        self.arguments = {}

    def search(self, **kwargs):
        self.arguments = dict(kwargs)

        return {
            "results": [
                {
                    "title": "深圳市官方消防通知",
                    "url": (
                        "https://yjgl.sz.gov.cn/"
                        "example/fire-notice"
                    ),
                    "content": (
                        "这是用于自动测试的官方网页摘要。"
                    ),
                    "published_date": "2026-01-02",
                    "raw_content": "",
                    "score": 0.95,
                },
                {
                    "title": "非HTTPS结果",
                    "url": (
                        "http://yjgl.sz.gov.cn/unsafe"
                    ),
                    "content": "这条结果必须被丢弃。",
                    "score": 0.5,
                },
                {
                    "title": "白名单外结果",
                    "url": "https://example.com/unsafe",
                    "content": "这条结果也必须被丢弃。",
                    "score": 0.5,
                },
            ]
        }


fake_client = FakeTavilyClient()
original_factory = (
    web_search_server.get_tavily_client
)

try:
    web_search_server.get_tavily_client = (
        lambda: fake_client
    )

    result = web_search_server.search_web(
        query="深圳消防最新政策",
        max_results=99,
        include_domains=[
            "gov.cn",
            "sz.gov.cn",
        ],
    )
finally:
    web_search_server.get_tavily_client = (
        original_factory
    )


assert fake_client.arguments["max_results"] == 5
assert fake_client.arguments[
    "include_raw_content"
] == "text"
assert len(result.results) == 1
assert result.results[0].domain == "yjgl.sz.gov.cn"

print("通过：结果上限、域名和URL协议均受到控制")


print("\n" + "=" * 70)
print("测试4：网页正文可以补全缺失的发布日期")

published_date, date_source = (
    web_search_server.extract_published_date(
        ("provider", ""),
        (
            "page_content",
            "本通知于2026年8月17日正式发布。",
        ),
    )
)

assert published_date == "2026-08-17"
assert date_source == "page_content"

print("通过：正文中的中文日期已被标准化提取")


print("\n" + "=" * 70)
print("测试5：中英文密钥占位符必须被识别")

assert is_placeholder_setting(
    "replace_with_your_tavily_api_key"
)
assert is_placeholder_setting(
    "这里换成真实密钥"
)
assert not is_placeholder_setting(
    "tvly-realistic-test-value-123456"
)

print("通过：英文占位符不会再被当成真实密钥")


print("\n" + "=" * 70)
print("测试6：IP地址和白名单外域名必须被阻止")

blocked_urls = [
    "https://127.0.0.1/private",
    "https://example.com/private",
]

for blocked_url in blocked_urls:
    try:
        validate_search_result_url(
            blocked_url,
            WEB_SEARCH_ALLOWED_DOMAINS,
        )
    except (ValueError, PermissionError):
        pass
    else:
        raise AssertionError(
            "危险URL没有被阻止："
            + blocked_url
        )

print("通过：IP地址和白名单外域名已被阻止")
print("\nMCP Web Search基础测试全部通过")
