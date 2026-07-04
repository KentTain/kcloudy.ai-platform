# AI 对话思考过程分片功能实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 AI 对话系统添加思考过程分片功能，通过 LangChain Callback 捕获推理链并流式展示

**架构：** 后端使用 ReasoningStepBuilder 管理推理栈，通过扩展 UIMessageChunkCallbackHandler 捕获事件；前端复用 Reasoning 组件实现 ThinkingBlock 展示可折叠思考过程

**技术栈：** Python 3.12 + FastAPI + LangChain (后端) | Vue 3 + TypeScript + AI SDK (前端)

---

## 文件结构

### 后端新增文件

1. **`server/python/src/extended/langchain/callbacks/reasoning_types.py`**
   - 职责：定义推理步骤类型枚举和数据结构
   - 大小：~50 行

2. **`server/python/src/extended/langchain/callbacks/reasoning_step_builder.py`**
   - 职责：推理步骤构建器，管理推理栈、过滤敏感信息、批量发送事件
   - 大小：~300 行

3. **`server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py`**
   - 职责：ReasoningStepBuilder 单元测试
   - 大小：~400 行

4. **`server/python/tests/ai/integration/test_thinking_process.py`**
   - 职责：思考过程集成测试
   - 大小：~150 行

### 后端修改文件

1. **`server/python/src/ai/controllers/v1/chat/event_types.py`**
   - 修改：添加 `THINKING_START`, `THINKING_DELTA`, `THINKING_END` 枚举值
   - 影响行数：+3 行

2. **`server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`**
   - 修改：添加 `on_chain_start`, `on_chain_end`, `on_llm_start`, `on_llm_end` 回调方法
   - 影响行数：+100 行

3. **`server/python/src/ai/controllers/v1/chat/llm.py`**
   - 修改：扩展 `_sse_generator()` 处理思考事件
   - 影响行数：+20 行

### 前端新增文件

1. **`web/vue/src/components/ai-elements/thinking/ThinkingBlock.vue`**
   - 职责：思考过程展示组件（基于 Reasoning 组件封装，添加步骤类型标签）
   - 大小：~60 行（复用现有 Reasoning 组件）

2. **`web/vue/tests/ai/unit/components/ThinkingBlock.test.ts`**
   - 职责：ThinkingBlock 组件测试
   - 大小：~150 行

3. **`web/vue/tests/ai/e2e/thinking-process.spec.ts`**
   - 职责：E2E 端到端测试
   - 大小：~100 行

### 前端修改文件

1. **`web/vue/src/ai/types/index.ts`**
   - 修改：添加 `ThinkingPart` 类型和 `ReasoningStepType` 类型
   - 影响行数：+30 行

2. **`web/vue/src/ai/composables/useChat.ts`**
   - 修改：添加 `processThinkingEvents()` 函数处理思考事件
   - 影响行数：+80 行

3. **`web/vue/src/ai/pages/ChatPage.vue`**
   - 修改：集成 ThinkingBlock 组件到消息渲染
   - 影响行数：+15 行

---

## 任务清单概览

| 任务 | 预计时间 | 关键产出 |
|------|---------|---------|
| 1. 定义推理步骤类型和数据结构 | 0.5 天 | ReasoningStepType 枚举、ReasoningStep 数据类 |
| 2. 扩展 EventType 枚举 | 0.2 天 | 新增 3 个思考事件类型 |
| 3. 实现 ReasoningStepBuilder 核心类 | 1 天 | 推理栈管理、敏感信息过滤、批量发送 |
| 4. 扩展 UIMessageChunkCallbackHandler | 0.5 天 | 新增 4 个回调方法 |
| 5. 扩展 SSE Generator | 0.3 天 | 处理思考事件流 |
| 6. 定义前端 ThinkingPart 类型 | 0.2 天 | TypeScript 类型定义 |
| 7. 实现 ThinkingBlock 组件 | 0.3 天 | 基于 Reasoning 的封装组件 |
| 8. 扩展 useChat 处理思考事件 | 0.5 天 | 思考事件合并和重组 |
| 9. 集成到 ChatPage | 0.2 天 | UI 集成 |
| 10. 编写后端单元测试 | 0.5 天 | 测试覆盖 ≥85% |
| 11. 编写集成测试和 E2E 测试 | 0.3 天 | 完整流程验证 |

**总计：** 4.5 天

---

## 任务 1：定义推理步骤类型和数据结构

**文件：**
- 创建：`server/python/src/extended/langchain/callbacks/reasoning_types.py`
- 测试：`server/python/tests/extended/langchain/callbacks/test_reasoning_types.py`

- [ ] **步骤 1：编写 ReasoningStepType 枚举测试**

创建测试文件：

```python
# server/python/tests/extended/langchain/callbacks/test_reasoning_types.py

import pytest
from extended.langchain.callbacks.reasoning_types import ReasoningStepType


class TestReasoningStepType:
    """ReasoningStepType 枚举测试"""

    def test_reasoning_step_type_values(self):
        """测试枚举值正确"""
        assert ReasoningStepType.REASONING.value == "reasoning"
        assert ReasoningStepType.DECISION.value == "decision"
        assert ReasoningStepType.TOOL_SELECTION.value == "tool_selection"
        assert ReasoningStepType.TOOL_EXECUTION.value == "tool_execution"
        assert ReasoningStepType.RESULT_ANALYSIS.value == "result_analysis"
        assert ReasoningStepType.ERROR_HANDLING.value == "error_handling"

    def test_reasoning_step_type_string_conversion(self):
        """测试字符串转换"""
        assert str(ReasoningStepType.REASONING) == "reasoning"
        assert ReasoningStepType("decision") == ReasoningStepType.DECISION
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_types.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'extended.langchain.callbacks.reasoning_types'`

- [ ] **步骤 3：创建 reasoning_types.py 文件**

```python
# server/python/src/extended/langchain/callbacks/reasoning_types.py

"""推理步骤类型定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class ReasoningStepType(str, Enum):
    """推理步骤类型枚举

    用于区分不同类型的推理步骤，帮助用户理解 AI 的思考过程。
    """

    REASONING = "reasoning"              # 推理分析
    DECISION = "decision"                # 决策制定
    TOOL_SELECTION = "tool_selection"    # 工具选择
    TOOL_EXECUTION = "tool_execution"    # 工具执行
    RESULT_ANALYSIS = "result_analysis"  # 结果分析
    ERROR_HANDLING = "error_handling"    # 错误处理


@dataclass
class ReasoningStep:
    """推理步骤数据结构

    表示推理过程中的一个步骤，包含步骤的基本信息和内容。

    Attributes:
        id: 步骤唯一标识符
        step_type: 步骤类型
        title: 步骤标题（可选）
        content: 步骤内容
        parent_id: 父步骤 ID（用于嵌套推理）
        metadata: 元数据
        created_at: 创建时间
    """

    id: str = field(default_factory=lambda: f"thinking-{uuid.uuid4().hex[:8]}")
    step_type: ReasoningStepType = ReasoningStepType.REASONING
    title: str | None = None
    content: str = ""
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式，用于 SSE 事件

        Returns:
            包含步骤信息的字典
        """
        result = {
            "id": self.id,
            "stepType": self.step_type.value,
        }
        if self.title:
            result["title"] = self.title
        if self.content:
            result["delta"] = self.content
        return result
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_types.py -v`

预期：PASS

- [ ] **步骤 5：编写 ReasoningStep 数据类测试**

在测试文件中添加：

```python
# server/python/tests/extended/langchain/callbacks/test_reasoning_types.py

# ... 现有导入 ...
from extended.langchain.callbacks.reasoning_types import ReasoningStep


class TestReasoningStep:
    """ReasoningStep 数据类测试"""

    def test_reasoning_step_default_values(self):
        """测试默认值"""
        step = ReasoningStep()
        assert step.id.startswith("thinking-")
        assert step.step_type == ReasoningStepType.REASONING
        assert step.title is None
        assert step.content == ""
        assert step.parent_id is None
        assert step.metadata == {}
        assert isinstance(step.created_at, datetime)

    def test_reasoning_step_custom_values(self):
        """测试自定义值"""
        step = ReasoningStep(
            step_type=ReasoningStepType.DECISION,
            title="分析问题",
            content="正在分析用户输入",
            parent_id="thinking-parent",
            metadata={"key": "value"},
        )
        assert step.step_type == ReasoningStepType.DECISION
        assert step.title == "分析问题"
        assert step.content == "正在分析用户输入"
        assert step.parent_id == "thinking-parent"
        assert step.metadata == {"key": "value"}

    def test_reasoning_step_to_dict(self):
        """测试转换为字典"""
        step = ReasoningStep(
            id="thinking-test",
            step_type=ReasoningStepType.TOOL_SELECTION,
            title="选择工具",
            content="选择天气查询工具",
        )
        result = step.to_dict()

        assert result["id"] == "thinking-test"
        assert result["stepType"] == "tool_selection"
        assert result["title"] == "选择工具"
        assert result["delta"] == "选择天气查询工具"
```

- [ ] **步骤 6：运行测试验证通过**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_types.py::TestReasoningStep -v`

预期：PASS

- [ ] **步骤 7：Commit**

```bash
git add server/python/src/extended/langchain/callbacks/reasoning_types.py
git add server/python/tests/extended/langchain/callbacks/test_reasoning_types.py
git commit -m "feat(ai): 添加推理步骤类型和数据结构

- 新增 ReasoningStepType 枚举定义 6 种推理类型
- 新增 ReasoningStep 数据类表示推理步骤
- 添加完整的单元测试覆盖
- 支持序列化为 SSE 事件格式

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 2：扩展 EventType 枚举

**文件：**
- 修改：`server/python/src/ai/controllers/v1/chat/event_types.py`
- 测试：`server/python/tests/ai/unit/controllers/v1/chat/test_event_types.py`

- [ ] **步骤 1：编写 EventType 扩展测试**

创建测试文件：

```python
# server/python/tests/ai/unit/controllers/v1/chat/test_event_types.py

import pytest
from ai.controllers.v1.chat.event_types import EventType


class TestEventTypeThinking:
    """EventType 思考事件测试"""

    def test_thinking_start_event_type(self):
        """测试 THINKING_START 事件类型"""
        assert hasattr(EventType, "THINKING_START")
        assert EventType.THINKING_START.value == "thinking-start"

    def test_thinking_delta_event_type(self):
        """测试 THINKING_DELTA 事件类型"""
        assert hasattr(EventType, "THINKING_DELTA")
        assert EventType.THINKING_DELTA.value == "thinking-delta"

    def test_thinking_end_event_type(self):
        """测试 THINKING_END 事件类型"""
        assert hasattr(EventType, "THINKING_END")
        assert EventType.THINKING_END.value == "thinking-end"

    def test_all_event_types_count(self):
        """测试事件类型总数"""
        # 原有 8 个 + 新增 3 个 = 11 个
        assert len(EventType) == 11
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest server/python/tests/ai/unit/controllers/v1/chat/test_event_types.py -v`

预期：FAIL，报错 `AttributeError: THINKING_START`

- [ ] **步骤 3：修改 event_types.py 添加思考事件类型**

```python
# server/python/src/ai/controllers/v1/chat/event_types.py

"""SSE 事件类型定义

AI SDK UIMessageChunk 标准事件类型。
"""

from enum import Enum


class EventType(str, Enum):
    """SSE 事件类型（AI SDK UIMessageChunk 标准）"""

    START = "start"
    TEXT_START = "text-start"
    TEXT_DELTA = "text-delta"
    TEXT_END = "text-end"
    TOOL_CALL = "tool-call"
    TOOL_RESULT = "tool-result"
    FINISH = "finish"
    ERROR = "error"

    # 思考过程事件
    THINKING_START = "thinking-start"    # 思考块开始
    THINKING_DELTA = "thinking-delta"    # 思考内容增量
    THINKING_END = "thinking-end"        # 思考块结束
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest server/python/tests/ai/unit/controllers/v1/chat/test_event_types.py -v`

预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/controllers/v1/chat/event_types.py
git add server/python/tests/ai/unit/controllers/v1/chat/test_event_types.py
git commit -m "feat(ai): 扩展 EventType 枚举添加思考过程事件类型

- 新增 THINKING_START 事件类型
- 新增 THINKING_DELTA 事件类型
- 新增 THINKING_END 事件类型
- 添加单元测试验证

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 3：实现 ReasoningStepBuilder 核心类

**文件：**
- 创建：`server/python/src/extended/langchain/callbacks/reasoning_step_builder.py`
- 测试：`server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py`

由于 ReasoningStepBuilder 代码量较大（~300 行），我将按照功能分块实现。

### 3.1 基础结构和初始化

- [ ] **步骤 1：编写 ReasoningStepBuilder 初始化测试**

```python
# server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py

import asyncio
import pytest
from extended.langchain.callbacks.reasoning_step_builder import ReasoningStepBuilder


@pytest.fixture
def event_queue():
    """创建事件队列 fixture"""
    return asyncio.Queue()


@pytest.fixture
def builder(event_queue):
    """创建 ReasoningStepBuilder fixture"""
    return ReasoningStepBuilder(event_queue)


class TestReasoningStepBuilderInit:
    """ReasoningStepBuilder 初始化测试"""

    def test_init_with_event_queue(self, event_queue):
        """测试使用事件队列初始化"""
        builder = ReasoningStepBuilder(event_queue)

        assert builder.event_queue == event_queue
        assert builder.step_stack == []
        assert builder._pending_deltas == []
        assert len(builder.sensitive_keywords) > 0

    def test_max_reasoning_depth_constant(self, builder):
        """测试最大推理深度常量"""
        assert ReasoningStepBuilder.MAX_REASONING_DEPTH == 10
        assert ReasoningStepBuilder.MAX_THINKING_LENGTH == 10000
        assert ReasoningStepBuilder.BATCH_SIZE == 5
        assert ReasoningStepBuilder.BATCH_INTERVAL == 0.1
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderInit -v`

预期：FAIL，报错 `ModuleNotFoundError`

- [ ] **步骤 3：创建 ReasoningStepBuilder 基础结构**

```python
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
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderInit -v`

预期：PASS

### 3.2 实现开始推理步骤

- [ ] **步骤 5：编写 start_reasoning_step 测试**

在测试文件中添加：

```python
# server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py

# ... 现有导入 ...
from extended.langchain.callbacks.reasoning_types import ReasoningStepType
from ai.controllers.v1.chat.event_types import EventType


class TestReasoningStepBuilderStartStep:
    """start_reasoning_step 测试"""

    @pytest.mark.asyncio
    async def test_start_reasoning_step_sends_event(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试开始推理步骤发送 thinking-start 事件"""
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.REASONING,
            title="分析问题"
        )

        assert step_id is not None
        assert step_id.startswith("thinking-")

        # 验证事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_START
        assert event["id"] == step_id
        assert event["title"] == "分析问题"
        assert event["stepType"] == "reasoning"

    @pytest.mark.asyncio
    async def test_start_reasoning_step_adds_to_stack(
        self, builder: ReasoningStepBuilder
    ):
        """测试开始推理步骤添加到栈"""
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.DECISION
        )

        assert len(builder.step_stack) == 1
        assert builder.step_stack[0].id == step_id
        assert builder.step_stack[0].step_type == ReasoningStepType.DECISION

    @pytest.mark.asyncio
    async def test_start_reasoning_step_max_depth_limit(
        self, builder: ReasoningStepBuilder
    ):
        """测试最大深度限制"""
        # 超过最大深度
        for i in range(15):
            step_id = await builder.start_reasoning_step(
                step_type=ReasoningStepType.REASONING
            )

            if i < ReasoningStepBuilder.MAX_REASONING_DEPTH:
                assert step_id is not None
            else:
                # 超过深度限制，应该返回空字符串
                assert step_id == ""

        # 栈深度应该被限制
        assert len(builder.step_stack) == ReasoningStepBuilder.MAX_REASONING_DEPTH
```

- [ ] **步骤 6：运行测试验证失败**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderStartStep -v`

预期：FAIL，报错 `AttributeError: 'ReasoningStepBuilder' object has no attribute 'start_reasoning_step'`

- [ ] **步骤 7：实现 start_reasoning_step 方法**

在 ReasoningStepBuilder 类中添加：

```python
# server/python/src/extended/langchain/callbacks/reasoning_step_builder.py

# ... 现有代码 ...

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
```

- [ ] **步骤 8：运行测试验证通过**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderStartStep -v`

预期：PASS

### 3.3 实现追加推理内容（含敏感信息过滤）

- [ ] **步骤 9：编写 append_reasoning_content 测试**

在测试文件中添加：

```python
# server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py

class TestReasoningStepBuilderAppendContent:
    """append_reasoning_content 测试"""

    @pytest.mark.asyncio
    async def test_append_reasoning_content_sends_delta(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试追加思考内容发送 thinking-delta 事件"""
        # 先开始一个步骤
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.REASONING
        )

        # 清空队列（移除 thinking-start）
        event_queue.get_nowait()

        # 追加内容
        await builder.append_reasoning_content("思考内容")

        # 验证 delta 事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_DELTA
        assert event["id"] == step_id
        assert event["delta"] == "思考内容"

    @pytest.mark.asyncio
    async def test_append_reasoning_content_filters_sensitive_keywords(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试敏感关键词过滤"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()  # 清空

        # 测试 API Key 过滤
        await builder.append_reasoning_content("api_key=sk-1234567890")
        assert event_queue.empty()  # 应该被过滤，不发送事件

    @pytest.mark.asyncio
    async def test_append_reasoning_content_filters_api_key_pattern(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试 API Key 格式过滤"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()

        # 测试 API Key 正则匹配
        await builder.append_reasoning_content("key: sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGH")
        assert event_queue.empty()

    @pytest.mark.asyncio
    async def test_append_reasoning_content_filters_json_field(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试 JSON 字段过滤"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()

        # 测试 JSON 字段检测
        await builder.append_reasoning_content('{"api_key": "secret123"}')
        assert event_queue.empty()

    @pytest.mark.asyncio
    async def test_append_reasoning_content_normal_content(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试正常内容通过"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()

        # 测试正常内容
        await builder.append_reasoning_content("正常思考内容")
        event = event_queue.get_nowait()
        assert event["delta"] == "正常思考内容"
```

- [ ] **步骤 10：运行测试验证失败**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderAppendContent -v`

预期：FAIL

- [ ] **步骤 11：实现 append_reasoning_content 和敏感信息过滤**

在 ReasoningStepBuilder 类中添加：

```python
# server/python/src/extended/langchain/callbacks/reasoning_step_builder.py

# ... 现有代码 ...

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
```

- [ ] **步骤 12：运行测试验证通过**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderAppendContent -v`

预期：PASS

### 3.4 实现结束推理步骤

- [ ] **步骤 13：编写 end_reasoning_step 测试**

在测试文件中添加：

```python
# server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py

class TestReasoningStepBuilderEndStep:
    """end_reasoning_step 测试"""

    @pytest.mark.asyncio
    async def test_end_reasoning_step_sends_end_event(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试结束推理步骤发送 thinking-end 事件"""
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.DECISION
        )

        # 清空队列
        while not event_queue.empty():
            event_queue.get_nowait()

        # 结束步骤
        await builder.end_reasoning_step()

        # 验证 end 事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_END
        assert event["id"] == step_id

    @pytest.mark.asyncio
    async def test_end_reasoning_step_pops_from_stack(
        self, builder: ReasoningStepBuilder
    ):
        """测试结束推理步骤从栈弹出"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        assert len(builder.step_stack) == 1

        await builder.end_reasoning_step()
        assert len(builder.step_stack) == 0

    @pytest.mark.asyncio
    async def test_end_reasoning_step_with_pending_deltas(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试结束步骤时发送剩余 delta"""
        step_id = await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()  # 清空 start

        # 追加少量内容（不触发批量发送）
        for i in range(3):  # 小于 BATCH_SIZE (5)
            await builder.append_reasoning_content(f"内容{i}")

        # 队列应该没有事件（未达到批量阈值）
        # 但在 end_reasoning_step 时应该发送

        # 清空队列
        while not event_queue.empty():
            event_queue.get_nowait()

        # 结束步骤
        await builder.end_reasoning_step()

        # 应该有一个 delta 事件（批量发送剩余内容）
        delta_event = event_queue.get_nowait()
        assert delta_event["type"] == EventType.THINKING_DELTA

        # 然后是 end 事件
        end_event = event_queue.get_nowait()
        assert end_event["type"] == EventType.THINKING_END
```

- [ ] **步骤 14：运行测试验证失败**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderEndStep -v`

预期：FAIL

- [ ] **步骤 15：实现 end_reasoning_step 方法**

在 ReasoningStepBuilder 类中添加：

```python
# server/python/src/extended/langchain/callbacks/reasoning_step_builder.py

# ... 现有代码 ...

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
```

- [ ] **步骤 16：运行测试验证通过**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py::TestReasoningStepBuilderEndStep -v`

预期：PASS

- [ ] **步骤 17：运行所有 ReasoningStepBuilder 测试**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py -v`

预期：所有测试 PASS

- [ ] **步骤 18：Commit**

```bash
git add server/python/src/extended/langchain/callbacks/reasoning_step_builder.py
git add server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py
git commit -m "feat(ai): 实现 ReasoningStepBuilder 核心类

- 实现推理步骤栈管理，支持最大 10 层嵌套
- 实现三层敏感信息过滤（关键词+正则+JSON）
- 实现批量发送优化，减少网络开销
- 添加完整的单元测试覆盖

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 4：扩展 UIMessageChunkCallbackHandler

**文件：**
- 修改：`server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`
- 测试：`server/python/tests/extended/langchain/callbacks/test_ui_message_chunk_callback.py`

- [ ] **步骤 1：读取现有 UIMessageChunkCallbackHandler 代码**

现有代码位置：`server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`

现有类实现了 4 个回调：
- `on_tool_start`
- `on_tool_end`
- `on_tool_error`
- `on_llm_new_token`

- [ ] **步骤 2：编写扩展回调测试**

在测试文件中添加：

```python
# server/python/tests/extended/langchain/callbacks/test_ui_message_chunk_callback.py

# ... 现有导入 ...
import uuid
from ai.controllers.v1.chat.event_types import EventType
from extended.langchain.callbacks.reasoning_types import ReasoningStepType


class TestUIMessageChunkCallbackHandlerThinking:
    """测试思考过程捕获功能"""

    @pytest.mark.asyncio
    async def test_on_chain_start_captures_decision(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_chain_start 捕获决策步骤"""
        run_id = uuid.uuid4()
        serialized = {"name": "agent_decision"}
        inputs = {"input": "用户问题"}

        await callback_handler.on_chain_start(
            serialized=serialized,
            inputs=inputs,
            run_id=run_id,
        )

        # 验证思考事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_START
        assert event["stepType"] == "decision"

    @pytest.mark.asyncio
    async def test_on_llm_start_captures_reasoning_after_first_call(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_llm_start 在第一次调用后捕获推理过程"""
        run_id = uuid.uuid4()

        # 第一次 LLM 调用
        await callback_handler.on_llm_start(
            serialized={},
            prompts=["分析问题"],
            run_id=run_id,
        )

        # 不应该创建思考步骤（第一次调用不创建）
        assert callback_handler.reasoning_builder.step_stack == []
        assert callback_handler.first_llm_call == False

        # 清空队列
        while not event_queue.empty():
            event_queue.get_nowait()

        # 第二次 LLM 调用（工具调用后）
        await callback_handler.on_llm_start(
            serialized={},
            prompts=["基于工具结果分析"],
            run_id=uuid.uuid4(),
        )

        # 应该创建思考步骤
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_START
        assert event["stepType"] == "result_analysis"
```

- [ ] **步骤 3：运行测试验证失败**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_ui_message_chunk_callback.py::TestUIMessageChunkCallbackHandlerThinking -v`

预期：FAIL，报错 `AttributeError: 'UIMessageChunkCallbackHandler' object has no attribute 'reasoning_builder'`

- [ ] **步骤 4：修改 UIMessageChunkCallbackHandler __init__**

修改 `__init__` 方法：

```python
# server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py

# ... 现有导入 ...
from extended.langchain.callbacks.reasoning_step_builder import ReasoningStepBuilder
from extended.langchain.callbacks.reasoning_types import ReasoningStepType

class UIMessageChunkCallbackHandler(AsyncCallbackHandler):
    """将 LangChain 事件转换为 AI SDK UIMessageChunk 格式

    扩展功能：
    - 支持推理步骤跟踪（on_chain_start/end）
    - 支持 LLM 思考过程捕获（on_llm_start/end）
    - 支持工具调用推理（on_tool_start/end）
    """

    def __init__(
        self,
        event_queue: asyncio.Queue,
        message_id: str = "",
        thinking_config: dict[str, Any] | None = None,
    ) -> None:
        """初始化回调处理器

        Args:
            event_queue: 事件队列，用于发送 SSE 事件
            message_id: 消息 ID，用于生成 text-delta 事件的 id
            thinking_config: 思考过程功能配置
        """
        super().__init__()
        self.event_queue = event_queue
        self._tool_call_ids: dict[str, str] = {}  # run_id -> tool_name 映射
        self.message_id = message_id
        self.full_content = ""  # 累积文本内容

        # 思考过程功能配置
        self.thinking_enabled = thinking_config.get("enabled", True) if thinking_config else True
        self.reasoning_builder = ReasoningStepBuilder(event_queue) if self.thinking_enabled else None
        self.first_llm_call = True  # 标记是否是第一次 LLM 调用
```

- [ ] **步骤 5：实现 on_chain_start 方法**

在类中添加新方法：

```python
    async def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """链式调用开始（Agent 决策、工具链等）

        捕获 Agent 的决策步骤和推理过程
        """
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 判断是否是 Agent 决策步骤
            chain_name = serialized.get("name", "")

            # 检查是否为 Agent 或决策相关的链
            if self._is_agent_decision(chain_name, metadata):
                # 提取决策上下文
                decision_context = self._extract_decision_context(inputs)

                # 开始推理步骤
                await self.reasoning_builder.start_reasoning_step(
                    step_type=ReasoningStepType.DECISION,
                    title=f"决策: {chain_name}",
                    metadata={
                        "run_id": str(run_id),
                        "parent_run_id": str(parent_run_id) if parent_run_id else None,
                        "chain_name": chain_name,
                    }
                )

                # 输出决策内容
                if decision_context:
                    await self.reasoning_builder.append_reasoning_content(
                        f"分析输入: {decision_context}\n"
                    )

        except Exception:
            _logger.exception("处理 chain_start 事件时出错")
```

- [ ] **步骤 6：实现辅助方法**

添加辅助方法：

```python
    def _is_agent_decision(self, chain_name: str, metadata: dict | None) -> bool:
        """判断是否是 Agent 决策步骤

        Args:
            chain_name: 链名称
            metadata: 元数据

        Returns:
            是否为决策步骤
        """
        # 检查名称中是否包含关键词
        decision_keywords = ["agent", "decision", "planner", "reasoning"]
        return any(kw in chain_name.lower() for kw in decision_keywords)

    def _extract_decision_context(self, inputs: dict[str, Any]) -> str:
        """提取决策上下文

        Args:
            inputs: 输入参数

        Returns:
            决策上下文字符串
        """
        if "input" in inputs:
            return str(inputs["input"])
        elif "query" in inputs:
            return str(inputs["query"])
        return ""
```

- [ ] **步骤 7：实现 on_chain_end 方法**

```python
    async def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """链式调用结束"""
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 结束当前活跃的推理步骤（如果有）
            if self.reasoning_builder.step_stack:
                # 输出决策结果
                if outputs:
                    result_summary = self._summarize_output(outputs)
                    await self.reasoning_builder.append_reasoning_content(
                        f"决策结果: {result_summary}\n"
                    )

                await self.reasoning_builder.end_reasoning_step()

        except Exception:
            _logger.exception("处理 chain_end 事件时出错")

    def _summarize_output(self, outputs: dict[str, Any]) -> str:
        """总结输出内容

        Args:
            outputs: 输出字典

        Returns:
            输出摘要
        """
        if "output" in outputs:
            output = outputs["output"]
            if isinstance(output, str):
                return output[:100] + "..." if len(output) > 100 else output
        return "完成"
```

- [ ] **步骤 8：实现 on_llm_start 和 on_llm_end 方法**

```python
    async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用开始

        区分：
        - 第一次 LLM 调用：生成思考过程
        - 后续 LLM 调用：可能是工具调用后的分析
        """
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 如果不是第一次调用，说明是工具调用后的推理
            if not self.first_llm_call:
                await self.reasoning_builder.start_reasoning_step(
                    step_type=ReasoningStepType.RESULT_ANALYSIS,
                    title="分析工具结果",
                    metadata={
                        "run_id": str(run_id),
                        "parent_run_id": str(parent_run_id) if parent_run_id else None,
                    }
                )

                # 输出分析提示
                if prompts:
                    prompt_summary = self._summarize_prompts(prompts)
                    await self.reasoning_builder.append_reasoning_content(
                        f"基于工具结果进行分析: {prompt_summary}\n"
                    )

            self.first_llm_call = False

        except Exception:
            _logger.exception("处理 llm_start 事件时出错")

    async def on_llm_end(
        self,
        response: Any,
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用结束"""
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 结束推理步骤（如果有）
            if self.reasoning_builder.step_stack:
                await self.reasoning_builder.end_reasoning_step()

        except Exception:
            _logger.exception("处理 llm_end 事件时出错")

    def _summarize_prompts(self, prompts: list[str]) -> str:
        """总结提示内容

        Args:
            prompts: 提示列表

        Returns:
            提示摘要
        """
        if not prompts:
            return ""
        # 取第一个提示的前 100 字符
        first_prompt = prompts[0]
        return first_prompt[:100] + "..." if len(first_prompt) > 100 else first_prompt
```

- [ ] **步骤 9：运行测试验证通过**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_ui_message_chunk_callback.py::TestUIMessageChunkCallbackHandlerThinking -v`

预期：PASS

- [ ] **步骤 10：运行所有回调测试**

运行：`uv run pytest server/python/tests/extended/langchain/callbacks/test_ui_message_chunk_callback.py -v`

预期：所有测试 PASS

- [ ] **步骤 11：Commit**

```bash
git add server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py
git add server/python/tests/extended/langchain/callbacks/test_ui_message_chunk_callback.py
git commit -m "feat(ai): 扩展 UIMessageChunkCallbackHandler 支持思考过程捕获

- 添加 on_chain_start/end 捕获 Agent 决策步骤
- 添加 on_llm_start/end 捕获 LLM 推理过程
- 集成 ReasoningStepBuilder 管理推理栈
- 使用 first_llm_call 标志区分首次和后续调用
- 添加完整的单元测试覆盖

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 5：扩展 SSE Generator

**文件：**
- 修改：`server/python/src/ai/controllers/v1/chat/llm.py`

- [ ] **步骤 1：读取现有 SSE Generator 代码**

现有代码位置：`server/python/src/ai/controllers/v1/chat/llm.py` 中的 `_sse_generator()` 函数

- [ ] **步骤 2：添加 thinking_started 标志**

在 `_sse_generator()` 函数中添加：

```python
# server/python/src/ai/controllers/v1/chat/llm.py

async def _sse_generator() -> AsyncGenerator[str, None]:
    """SSE 事件生成器"""
    event_queue: asyncio.Queue = asyncio.Queue()
    text_started = False
    thinking_started = False  # 新增：思考块状态标志

    # ... 现有代码 ...
```

- [ ] **步骤 3：处理思考事件**

在事件处理循环中添加：

```python
    async for event in event_generator:
        event_type = event.get("type")

        # 处理思考事件
        if event_type == EventType.THINKING_START:
            thinking_started = True
            yield f"event: thinking-start\ndata: {json.dumps(event)}\n\n"

        elif event_type == EventType.THINKING_DELTA:
            yield f"event: thinking-delta\ndata: {json.dumps(event)}\n\n"

        elif event_type == EventType.THINKING_END:
            thinking_started = False
            yield f"event: thinking-end\ndata: {json.dumps(event)}\n\n"

        # ... 现有事件处理 ...

        elif event_type == EventType.FINISH:
            # 确保思考块正确关闭
            if thinking_started:
                # 发送 thinking-end 事件
                thinking_end_event = {
                    "type": EventType.THINKING_END,
                    "id": event.get("id", ""),
                }
                yield f"event: thinking-end\ndata: {json.dumps(thinking_end_event)}\n\n"

            # 发送 finish 事件
            yield f"event: finish\ndata: {json.dumps(event)}\n\n"
            break
```

- [ ] **步骤 4：测试 SSE Generator**

手动测试或编写集成测试验证思考事件流。

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/controllers/v1/chat/llm.py
git commit -m "feat(ai): 扩展 SSE Generator 支持思考事件流

- 添加 thinking_started 状态标志
- 处理 THINKING_START/DELTA/END 事件
- 确保 FINISH 事件前正确关闭思考块

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 6：定义前端 ThinkingPart 类型

**文件：**
- 修改：`web/vue/src/ai/types/index.ts`

- [ ] **步骤 1：定义 ReasoningStepType 类型**

```typescript
// web/vue/src/ai/types/index.ts

// 推理步骤类型
export type ReasoningStepType =
  | "reasoning"
  | "decision"
  | "tool_selection"
  | "tool_execution"
  | "result_analysis"
  | "error_handling"

// 消息部分类型
export type UIMessagePartType =
  | "thinking"  // 新增
  | "text"
  | "image"
  | "tool-call"
  | "tool-result"

// 思考部分
export interface ThinkingPart extends UIMessagePartBase {
  type: "thinking"
  thinking: string
  title?: string
  stepType?: ReasoningStepType
}

// 更新 UIMessagePart 联合类型
export type UIMessagePart = TextPart | ImagePart | ToolCallPart | ToolResultPart | ThinkingPart
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/ai/types/index.ts
git commit -m "feat(ai): 添加 ThinkingPart 类型定义

- 新增 ReasoningStepType 类型
- 扩展 UIMessagePartType 包含 thinking
- 新增 ThinkingPart 接口
- 更新 UIMessagePart 联合类型

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 7：实现 ThinkingBlock 组件

**文件：**
- 创建：`web/vue/src/components/ai-elements/thinking/ThinkingBlock.vue`
- 测试：`web/vue/tests/ai/unit/components/ThinkingBlock.test.ts`

**重要说明：** 此组件基于现有 Reasoning 组件封装，复用其折叠功能，仅添加步骤类型标签。

- [ ] **步骤 1：创建 ThinkingBlock 组件**

```vue
<!-- web/vue/src/components/ai-elements/thinking/ThinkingBlock.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import { Reasoning, ReasoningTrigger, ReasoningContent } from '@/components/ai-elements/reasoning'
import { Badge } from '@/components'
import type { ReasoningStepType } from '@/ai/types'

interface Props {
  thinking: string
  title?: string
  stepType?: ReasoningStepType
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isStreaming: false,
})

// 步骤类型颜色映射
const stepTypeColors: Record<ReasoningStepType, string> = {
  reasoning: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  decision: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  tool_selection: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  tool_execution: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  result_analysis: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  error_handling: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
}

// 步骤类型标签映射
const stepTypeLabels: Record<ReasoningStepType, string> = {
  reasoning: '推理分析',
  decision: '决策制定',
  tool_selection: '工具选择',
  tool_execution: '工具执行',
  result_analysis: '结果分析',
  error_handling: '错误处理',
}

const badgeClass = computed(() => {
  if (!props.stepType) return ''
  return stepTypeColors[props.stepType]
})

const badgeLabel = computed(() => {
  if (!props.stepType) return ''
  return stepTypeLabels[props.stepType]
})
</script>

<template>
  <Reasoning :is-streaming="isStreaming">
    <ReasoningTrigger>
      <div class="flex items-center gap-2">
        <Badge v-if="stepType" :class="badgeClass" variant="outline">
          {{ badgeLabel }}
        </Badge>
        <span v-if="title" class="text-sm font-medium">{{ title }}</span>
      </div>
    </ReasoningTrigger>

    <ReasoningContent>
      <div class="whitespace-pre-wrap text-sm">{{ thinking }}</div>
    </ReasoningContent>
  </Reasoning>
</template>
```

- [ ] **步骤 2：创建组件测试**

```typescript
// web/vue/tests/ai/unit/components/ThinkingBlock.test.ts

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ThinkingBlock from '@/components/ai-elements/thinking/ThinkingBlock.vue'

describe('ThinkingBlock', () => {
  it('renders with default props', () => {
    const wrapper = mount(ThinkingBlock, {
      props: {
        thinking: '思考内容',
      },
    })

    expect(wrapper.text()).toContain('思考内容')
  })

  it('renders with step type badge', () => {
    const wrapper = mount(ThinkingBlock, {
      props: {
        thinking: '推理分析内容',
        stepType: 'reasoning',
        title: '分析问题',
      },
    })

    expect(wrapper.text()).toContain('推理分析')
    expect(wrapper.text()).toContain('分析问题')
  })

  it('applies correct badge color for each step type', () => {
    const stepTypes = [
      { type: 'reasoning' as const, expectedClass: 'bg-blue-100' },
      { type: 'decision' as const, expectedClass: 'bg-purple-100' },
      { type: 'tool_selection' as const, expectedClass: 'bg-orange-100' },
    ]

    stepTypes.forEach(({ type, expectedClass }) => {
      const wrapper = mount(ThinkingBlock, {
        props: {
          thinking: '内容',
          stepType: type,
        },
      })

      const badge = wrapper.find('[variant="outline"]')
      expect(badge.classes().join(' ')).toContain(expectedClass)
    })
  })
})
```

- [ ] **步骤 3：运行测试**

```bash
pnpm test:unit web/vue/tests/ai/unit/components/ThinkingBlock.test.ts --run
```

- [ ] **步骤 4：导出组件**

```typescript
// web/vue/src/components/ai-elements/thinking/index.ts
export { default as ThinkingBlock } from './ThinkingBlock.vue'
```

- [ ] **步骤 5：Commit**

```bash
git add web/vue/src/components/ai-elements/thinking/
git add web/vue/tests/ai/unit/components/ThinkingBlock.test.ts
git commit -m "feat(ai): 实现 ThinkingBlock 组件

- 基于 Reasoning 组件封装，复用折叠功能
- 添加步骤类型标签和颜色编码
- 支持 6 种推理步骤类型
- 添加组件单元测试

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 8：扩展 useChat 处理思考事件

**文件：**
- 修改：`web/vue/src/ai/composables/useChat.ts`

- [ ] **步骤 1：添加 processThinkingEvents 函数**

```typescript
// web/vue/src/ai/composables/useChat.ts

function processThinkingEvents(messages: UIMessage[]): UIMessage[] {
  /** 处理思考事件，合并 thinking-delta */

  return messages.map((message) => {
    if (!message.parts) return message

    // 按 ID 分组合并 thinking-delta
    const thinkingMap = new Map<string, {
      id: string
      thinking: string
      title?: string
      stepType?: ReasoningStepType
    }>()

    const processedParts: UIMessagePart[] = []

    message.parts.forEach((part) => {
      if (part.type === 'thinking') {
        const thinkingPart = part as ThinkingPart
        const id = part.id || 'default'

        // 累积思考内容
        if (thinkingMap.has(id)) {
          const existing = thinkingMap.get(id)!
          existing.thinking += thinkingPart.thinking
        } else {
          thinkingMap.set(id, {
            id,
            thinking: thinkingPart.thinking,
            title: thinkingPart.title,
            stepType: thinkingPart.stepType,
          })
        }
      } else {
        processedParts.push(part)
      }
    })

    // 将合并后的思考块添加到 parts 开头
    const thinkingParts: ThinkingPart[] = Array.from(thinkingMap.values()).map(
      ({ id, thinking, title, stepType }) => ({
        type: 'thinking' as const,
        id,
        thinking: thinking.slice(0, 10000), // 限制长度 10k 字符
        title,
        stepType,
      })
    )

    // 重组 parts：思考 → 工具调用 → 正文
    const toolCallParts = processedParts.filter((p) => p.type === 'tool-call')
    const toolResultParts = processedParts.filter((p) => p.type === 'tool-result')
    const textParts = processedParts.filter((p) => p.type === 'text')

    return {
      ...message,
      parts: [
        ...thinkingParts,
        ...toolCallParts,
        ...toolResultParts,
        ...textParts,
      ],
    }
  })
}
```

- [ ] **步骤 2：在 watchEffect 中应用处理**

```typescript
// 在现有的 watchEffect 中修改
watchEffect(() => {
  if (chat.messages) {
    // 处理思考事件
    const processedMessages = processThinkingEvents(chat.messages)
    messages.value = processedMessages
  }
})
```

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/ai/composables/useChat.ts
git commit -m "feat(ai): 扩展 useChat 处理思考事件

- 实现 processThinkingEvents 函数
- 按 ID 分组合并 thinking-delta
- 限制思考内容长度 10k 字符
- 重组 parts 顺序：思考 → 工具调用 → 正文

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 9：集成到 ChatPage

**文件：**
- 修改：`web/vue/src/ai/pages/ChatPage.vue`

- [ ] **步骤 1：导入 ThinkingBlock 组件**

```typescript
// web/vue/src/ai/pages/ChatPage.vue

import { ThinkingBlock } from '@/components/ai-elements/thinking'
```

- [ ] **步骤 2：在消息渲染中添加思考块**

```vue
<template>
  <!-- ... 现有代码 ... -->
  <div v-for="part in message.parts" :key="part.id">
    <!-- 思考块展示 -->
    <ThinkingBlock
      v-if="part.type === 'thinking'"
      :thinking="(part as ThinkingPart).thinking"
      :title="(part as ThinkingPart).title"
      :step-type="(part as ThinkingPart).stepType"
      :is-streaming="isStreaming"
    />

    <!-- 工具调用 -->
    <div v-else-if="part.type === 'tool-call'">
      <!-- ... 现有工具调用代码 ... -->
    </div>

    <!-- 正文内容 -->
    <div v-else-if="part.type === 'text'">
      <!-- ... 现有正文代码 ... -->
    </div>
  </div>
</template>
```

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/ai/pages/ChatPage.vue
git commit -m "feat(ai): 集成 ThinkingBlock 到聊天页面

- 导入 ThinkingBlock 组件
- 在消息渲染中添加思考块展示
- 思考块显示在工具调用之前

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 任务 10：编写后端单元测试

**文件：**
- 测试：已在任务 1-4 中完成

**验证测试覆盖率：**

```bash
# 运行所有后端测试并生成覆盖率报告
cd server/python
uv run pytest tests/extended/langchain/callbacks/ -v --cov=src/extended/langchain/callbacks --cov-report=term-missing
```

**目标：** 覆盖率 ≥ 85%

---

## 任务 11：编写集成测试和 E2E 测试

### 11.1 集成测试

**文件：**
- 创建：`server/python/tests/ai/integration/test_thinking_process.py`

- [ ] **步骤 1：编写集成测试**

```python
# server/python/tests/ai/integration/test_thinking_process.py

import pytest
from ai.controllers.v1.chat.llm import chat_stream
from ai.controllers.v1.chat.event_types import EventType


@pytest.mark.asyncio
async def test_thinking_process_sse_events():
    """测试完整 SSE 事件流"""
    # ... 测试代码 ...
    pass


@pytest.mark.asyncio
async def test_sensitive_info_filtering():
    """测试敏感信息过滤效果"""
    # ... 测试代码 ...
    pass
```

- [ ] **步骤 2：运行集成测试**

```bash
cd server/python
uv run pytest tests/ai/integration/test_thinking_process.py -v
```

### 11.2 E2E 测试

**文件：**
- 创建：`web/vue/tests/ai/e2e/thinking-process.spec.ts`

- [ ] **步骤 3：编写 E2E 测试**

```typescript
// web/vue/tests/ai/e2e/thinking-process.spec.ts

import { test, expect } from '@playwright/test'

test('思考过程块正确显示', async ({ page }) => {
  // ... 测试代码 ...
})

test('思考块折叠/展开交互', async ({ page }) => {
  // ... 测试代码 ...
})
```

- [ ] **步骤 4：运行 E2E 测试**

```bash
pnpm test:e2e web/vue/tests/ai/e2e/thinking-process.spec.ts
```

- [ ] **步骤 5：Commit 测试文件**

```bash
git add server/python/tests/ai/integration/test_thinking_process.py
git add web/vue/tests/ai/e2e/thinking-process.spec.ts
git commit -m "test(ai): 添加思考过程集成测试和 E2E 测试

- 添加完整 SSE 事件流集成测试
- 添加敏感信息过滤测试
- 添加 E2E 用户交互测试

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 验证清单

完成所有任务后，运行以下验证：

### 单元测试

```bash
# 后端测试
cd server/python
uv run pytest tests/extended/langchain/callbacks/ -v

# 前端测试
cd web/vue
pnpm test:unit --run
```

### 集成测试

```bash
# 后端集成测试
cd server/python
uv run pytest tests/ai/integration/test_thinking_process.py -v
```

### E2E 测试

```bash
# 端到端测试
cd web/vue
pnpm test:e2e tests/ai/e2e/thinking-process.spec.ts
```

### 手动验证

1. 启动后端服务：`cd server/python && uv run python manage.py runserver`
2. 启动前端服务：`cd web/vue && pnpm dev`
3. 发送需要推理的问题：`帮我分析一下明天北京的天气趋势`
4. 验证思考过程块正确显示且可折叠

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 | 优先级 |
|------|------|----------|--------|
| 敏感信息泄露 | 高 | 三层过滤机制 + 严格模式 + 测试覆盖 | P0 |
| 性能影响 | 中 | 批量发送 + 深度限制 + 异步处理 | P1 |
| 推理嵌套过深 | 中 | 最大深度限制 10 层 + 日志记录 | P1 |
| 前端内存溢出 | 中 | 内容长度限制 10k 字符 | P2 |

---

## 验收标准

- [ ] 所有单元测试通过（覆盖率：后端 ≥ 85%，前端 ≥ 75%）
- [ ] 集成测试通过
- [ ] E2E 测试通过
- [ ] 敏感信息过滤有效（测试覆盖所有规则）
- [ ] 性能无明显下降（批量发送效率 ≥ 60%）
- [ ] UI 展示正确（思考块、步骤标签、折叠交互）
- [ ] 代码审查通过
