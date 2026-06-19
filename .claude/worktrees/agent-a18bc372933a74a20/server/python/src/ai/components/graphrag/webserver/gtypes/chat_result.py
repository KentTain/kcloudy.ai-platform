"""GraphRAG Web 服务器响应结果类型定义。

GraphRAG Web Server response result type definitions.
"""

import asyncio
from typing import Any

from pydantic import BaseModel


class SearchResult(BaseModel):
    """
    搜索结果类。

    Search result class.
    """

    response: str | dict[str, Any] | list[dict[str, Any]]
    # 上下文窗口中的实际文本字符串,由 context_data 构建 / Actual text strings that are in the context window, built from context_data
    context_text: str | list[str] | dict[str, str] = None
    completion_time: float = None
    llm_calls: int = None
    prompt_tokens: int = None


class TaskResult(BaseModel):
    """
    任务结果类。

    Task result class.
    """

    taskId: str
    status: str = "running"  # running, done
    log: str | None = None
    start_time: int | None = None
    end_time: int | None = None
    ext_info: dict | None = None
    progress: int | None = None
    update_time: int | None = None
    thread_info: dict = {}
    token_info: dict = {}


class TypedFuture(asyncio.Future):
    """
    类型化的异步 Future 类。

    Typed asynchronous Future class.
    """
