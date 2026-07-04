# server/python/src/extended/langchain/callbacks/reasoning_step_builder.py

"""推理步骤构建器

负责构建推理步骤并生成 thinking-delta 事件。
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

from loguru import logger

from ai.controllers.v1.chat.event_types import EventType
from extended.langchain.callbacks.reasoning_types import ReasoningStep, ReasoningStepType

_logger = logger.bind(name=__name__)


class ReasoningStepBuilder:
    """推理步骤构建器

    职责：
    - 跟踪 LangChain 执行流程中的推理步骤
    - 构建推理树结构（支持嵌套推理）
    - 过滤敏感信息
    - 生成符合 AI SDK 标准的 thinking-delta 事件

    Attributes:
        MAX_REASONING_DEPTH: 最大推理嵌套深度
        MAX_THINKING_LENGTH: 单个思考块最大字符数
        BATCH_SIZE: 批量发送 delta 数量
        BATCH_INTERVAL: 批量发送间隔（秒）
    """

    MAX_REASONING_DEPTH = 10
    MAX_THINKING_LENGTH = 10000
    BATCH_SIZE = 5
    BATCH_INTERVAL = 0.1

    def __init__(self, event_queue: asyncio.Queue) -> None:
        """初始化推理步骤构建器

        Args:
            event_queue: 事件队列，用于发送 SSE 事件
        """
        self.event_queue = event_queue

        # 推理步骤栈：用于跟踪当前活跃的推理层级
        self.step_stack: list[ReasoningStep] = []

        # 批量发送优化
        self._pending_deltas: list[str] = []
        self._last_send_time = time.time()

        # 敏感信息过滤关键词列表
        self.sensitive_keywords = [
            "api_key", "password", "token", "secret", "credential",
            "private_key", "access_key", "auth", "authorization"
        ]

    async def start_reasoning_step(
        self,
        step_type: ReasoningStepType,
        title: str | None = None,
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """开始一个新的推理步骤

        Args:
            step_type: 步骤类型
            title: 步骤标题
            parent_id: 父步骤 ID（用于嵌套推理）
            metadata: 元数据

        Returns:
            步骤 ID，如果超过深度限制则返回空字符串
        """
        # 深度检查
        if len(self.step_stack) >= self.MAX_REASONING_DEPTH:
            _logger.warning(f"推理嵌套深度超过限制 {self.MAX_REASONING_DEPTH}，跳过")
            return ""

        step = ReasoningStep(
            step_type=step_type,
            title=title,
            parent_id=parent_id or (self.step_stack[-1].id if self.step_stack else None),
            metadata=metadata or {},
        )

        self.step_stack.append(step)

        # 发送 thinking-start 事件
        event = {
            "type": EventType.THINKING_START,
            "id": step.id,
            "title": step.title,
            "stepType": step.step_type.value,
        }
        await self.event_queue.put(event)

        _logger.info(
            "reasoning_step_started",
            step_id=step.id,
            step_type=step_type.value,
            title=title,
            stack_depth=len(self.step_stack),
        )

        return step.id

    async def append_reasoning_content(self, content: str) -> None:
        """向当前活跃的推理步骤追加内容

        Args:
            content: 思考内容片段
        """
        if not self.step_stack:
            _logger.warning("没有活跃的推理步骤，无法追加内容")
            return

        current_step = self.step_stack[-1]

        # 敏感信息过滤
        filtered_content = self._filter_sensitive_info(content)
        if not filtered_content:
            return

        # 长度限制
        if len(current_step.content) + len(filtered_content) > self.MAX_THINKING_LENGTH:
            _logger.warning(f"思考内容超过最大长度 {self.MAX_THINKING_LENGTH}，截断")
            filtered_content = filtered_content[:self.MAX_THINKING_LENGTH - len(current_step.content)]

        current_step.content += filtered_content
        self._pending_deltas.append(filtered_content)

        # 批量发送逻辑
        should_send = (
            len(self._pending_deltas) >= self.BATCH_SIZE or
            time.time() - self._last_send_time >= self.BATCH_INTERVAL
        )

        if should_send:
            combined_delta = ''.join(self._pending_deltas)
            event = {
                "type": EventType.THINKING_DELTA,
                "id": current_step.id,
                "delta": combined_delta,
            }
            await self.event_queue.put(event)
            self._pending_deltas = []
            self._last_send_time = time.time()

    def _filter_sensitive_info(self, content: str) -> str:
        """过滤敏感信息（三层检测）

        Args:
            content: 原始内容

        Returns:
            过滤后的内容，如果包含敏感信息则返回空字符串
        """
        # 1. 关键词过滤
        for keyword in self.sensitive_keywords:
            if keyword in content.lower():
                _logger.warning(f"检测到敏感关键词: {keyword}")
                return ""

        # 2. 正则匹配 API Key 格式
        api_key_pattern = re.compile(r'sk-[a-zA-Z0-9]{48}')
        if api_key_pattern.search(content):
            _logger.warning("检测到 API Key 格式")
            return ""

        # 3. JSON 字段检测
        try:
            if '{' in content and '}' in content:
                potential_json = content[content.index('{'):content.rindex('}')+1]
                data = json.loads(potential_json)

                sensitive_fields = ['api_key', 'password', 'token', 'secret']
                for field in sensitive_fields:
                    if field in data:
                        _logger.warning(f"检测到敏感字段: {field}")
                        return ""
        except (json.JSONDecodeError, ValueError):
            pass  # 不是 JSON，继续

        return content

    async def end_reasoning_step(self, step_id: str | None = None) -> None:
        """结束推理步骤

        Args:
            step_id: 要结束的步骤 ID（None 表示结束当前步骤）
        """
        if not self.step_stack:
            return

        # 发送剩余的 delta
        if self._pending_deltas:
            combined_delta = ''.join(self._pending_deltas)
            current_step = self.step_stack[-1]
            event = {
                "type": EventType.THINKING_DELTA,
                "id": current_step.id,
                "delta": combined_delta,
            }
            await self.event_queue.put(event)
            self._pending_deltas = []

        # 发送 thinking-end 事件
        current_step = self.step_stack.pop()
        event = {
            "type": EventType.THINKING_END,
            "id": current_step.id,
        }
        await self.event_queue.put(event)

        _logger.info(
            "reasoning_step_completed",
            step_id=current_step.id,
            content_length=len(current_step.content),
        )
