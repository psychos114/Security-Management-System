import atexit
import asyncio
from concurrent.futures import Future
from dataclasses import dataclass
from datetime import timedelta
import json
from queue import Empty, Queue
import sys
from threading import Event, Lock, Thread

from mcp import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    stdio_client,
)

from backend.app.core.config import (
    PROJECT_ROOT,
    WEB_SEARCH_TIMEOUT_SECONDS,
)


@dataclass
class _ToolRequest:
    tool_name: str
    arguments: dict[str, object] | None
    future: Future


_STOP_WORKER = object()


class WebSearchMCPClient:
    """通过一个长驻stdio会话调用本地Web Search MCP。"""

    def __init__(self):
        self._requests = Queue()
        self._ready = Event()
        self._start_lock = Lock()
        self._thread = None
        self._startup_error = None
        self._closed = False
        atexit.register(self.close)

    def _server_parameters(
        self,
    ) -> StdioServerParameters:
        return StdioServerParameters(
            command=sys.executable,
            args=[
                "-m",
                (
                    "backend.app.mcp_servers."
                    "web_search_server"
                ),
            ],
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
            encoding_error_handler="replace",
        )

    @staticmethod
    def _extract_structured_content(
        result,
    ) -> dict[str, object]:
        if result.isError:
            error_text = "MCP工具调用失败"

            for item in result.content:
                text = getattr(item, "text", "")
                if text:
                    error_text = str(text)
                    break

            raise RuntimeError(error_text)

        structured_content = (
            result.structuredContent
        )

        if isinstance(
            structured_content,
            dict,
        ):
            return dict(structured_content)

        for item in result.content:
            text = getattr(item, "text", "")

            if not text:
                continue

            parsed = json.loads(str(text))

            if isinstance(parsed, dict):
                return parsed

        raise RuntimeError(
            "MCP工具没有返回结构化数据"
        )

    async def _session_worker(self) -> None:
        """在专用事件循环中持有并复用MCP会话。"""

        try:
            async with stdio_client(
                self._server_parameters()
            ) as (read_stream, write_stream):
                async with ClientSession(
                    read_stream,
                    write_stream,
                ) as session:
                    await session.initialize()
                    self._ready.set()

                    while True:
                        request = await asyncio.to_thread(
                            self._requests.get
                        )

                        if request is _STOP_WORKER:
                            break

                        if not isinstance(
                            request,
                            _ToolRequest,
                        ):
                            continue

                        try:
                            result = await session.call_tool(
                                request.tool_name,
                                arguments=request.arguments,
                                read_timeout_seconds=(
                                    timedelta(
                                        seconds=(
                                            WEB_SEARCH_TIMEOUT_SECONDS
                                            + 10
                                        )
                                    )
                                ),
                            )
                            if not request.future.done():
                                request.future.set_result(
                                    result
                                )
                        except Exception as error:
                            if not request.future.done():
                                request.future.set_exception(
                                    error
                                )

        except Exception as error:
            self._startup_error = error
            self._ready.set()
            self._fail_pending_requests(error)

    def _fail_pending_requests(
        self,
        error: Exception,
    ) -> None:
        while True:
            try:
                request = self._requests.get_nowait()
            except Empty:
                return

            if (
                isinstance(request, _ToolRequest)
                and not request.future.done()
            ):
                request.future.set_exception(error)

    def _run_worker(self) -> None:
        asyncio.run(self._session_worker())

    def _ensure_started(self) -> None:
        if self._closed:
            raise RuntimeError(
                "Web Search MCP客户端已经关闭"
            )

        if self._thread and self._thread.is_alive():
            return

        with self._start_lock:
            if self._thread and self._thread.is_alive():
                return

            self._ready.clear()
            self._startup_error = None
            self._thread = Thread(
                target=self._run_worker,
                name="web-search-mcp-client",
                daemon=True,
            )
            self._thread.start()

            ready_timeout = (
                WEB_SEARCH_TIMEOUT_SECONDS + 10
            )

            if not self._ready.wait(ready_timeout):
                raise TimeoutError(
                    "Web Search MCP服务启动超时"
                )

            if self._startup_error is not None:
                raise RuntimeError(
                    "Web Search MCP服务启动失败"
                ) from self._startup_error

    def _submit_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, object] | None = None,
    ) -> Future:
        self._ensure_started()
        future = Future()
        self._requests.put(
            _ToolRequest(
                tool_name=tool_name,
                arguments=arguments,
                future=future,
            )
        )
        return future

    def _call_tool(
        self,
        tool_name: str,
        arguments: dict[str, object] | None = None,
    ) -> dict[str, object]:
        future = self._submit_tool_call(
            tool_name,
            arguments,
        )
        result = future.result(
            timeout=WEB_SEARCH_TIMEOUT_SECONDS + 10
        )
        return self._extract_structured_content(result)

    async def _call_tool_async(
        self,
        tool_name: str,
        arguments: dict[str, object] | None = None,
    ) -> dict[str, object]:
        future = self._submit_tool_call(
            tool_name,
            arguments,
        )
        result = await asyncio.wait_for(
            asyncio.wrap_future(future),
            timeout=WEB_SEARCH_TIMEOUT_SECONDS + 10,
        )
        return self._extract_structured_content(result)

    def health(self) -> dict[str, object]:
        """启动MCP子进程并检查协议连接。"""

        return self._call_tool(
            "web_search_health"
        )

    async def ahealth(self) -> dict[str, object]:
        """在已有事件循环中安全检查MCP连接。"""

        return await self._call_tool_async(
            "web_search_health"
        )

    def search(
        self,
        *,
        query: str,
        max_results: int,
        include_domains: list[str],
    ) -> dict[str, object]:
        """通过MCP调用一次受控搜索。"""

        return self._call_tool(
            "search_web",
            {
                "query": query,
                "max_results": max_results,
                "include_domains": (
                    include_domains
                ),
            },
        )

    async def asearch(
        self,
        *,
        query: str,
        max_results: int,
        include_domains: list[str],
    ) -> dict[str, object]:
        """在异步端点中安全复用长驻MCP会话。"""

        return await self._call_tool_async(
            "search_web",
            {
                "query": query,
                "max_results": max_results,
                "include_domains": (
                    include_domains
                ),
            },
        )

    def close(self) -> None:
        """关闭长驻MCP会话和子进程。"""

        with self._start_lock:
            thread = self._thread

            if self._closed:
                return

            self._closed = True

            if not thread or not thread.is_alive():
                return

            self._requests.put(_STOP_WORKER)

        thread.join(
            timeout=WEB_SEARCH_TIMEOUT_SECONDS + 10
        )
