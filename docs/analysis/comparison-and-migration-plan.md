# 对话接口对比分析：Hermes vs AI Platform

## 一、架构对比

### 1.1 整体架构差异

| 维度 | Hermes | AI Platform |
|------|--------|-------------|
| **架构风格** | 事件驱动 + 适配器模式 | 服务层 + 数据库持久化 |
| **核心组件** | AIAgent + Conversation Loop | ChatService + ConversationService |
| **消息模型** | 内存中的消息列表 + 可选持久化 | 数据库持久化 (PostgreSQL) |
| **流事件** | 结构化流事件 (dataclass) | 简单的 SSE 流式响应 |
| **平台支持** | 多平台适配器 | 单一 Web 平台 |

### 1.2 核心流程对比

#### Hermes 流程

```
用户消息 → Platform Adapter → Gateway
         → StreamEvents → AIAgent.run_conversation()
         → Tool Execution → LLM API
         → 流式回调 → Platform Adapter → 用户
```

#### AI Platform 流程

```
用户消息 → API Controller → ChatService
         → ConversationService → LLMService.stream()
         → SSE 响应 → 前端
```

---

## 二、功能差距分析

### 2.1 核心功能缺失项

| 功能 | Hermes | AI Platform | 差距评估 |
|------|--------|-------------|---------|
| **工具循环** | ✅ 多轮工具调用 | ❌ 未实现 | 🔴 严重 |
| **流事件系统** | ✅ 结构化事件 | ⚠️ 简单流式 | 🟡 中等 |
| **对话中断** | ✅ 支持 | ❌ 未实现 | 🟡 中等 |
| **对话引导** | ✅ Steering | ❌ 未实现 | 🟡 中等 |
| **对话压缩** | ✅ 自动压缩 | ❌ 未实现 | 🟡 中等 |
| **多模态支持** | ✅ 完整 | ⚠️ 部分 | 🟡 中等 |
| **平台适配器** | ✅ 多平台 | ❌ 单平台 | 🟢 低 |
| **会话持久化** | ⚠️ 可选 | ✅ 强制 | - |
| **消息分支** | ✅ 支持 | ❌ 未实现 | 🟢 低 |
| **推理过程** | ✅ thinking blocks | ❌ 未实现 | 🟡 中等 |

### 2.2 工具循环实现差距

**Hermes 工具循环：**

```python
# 支持多轮工具调用
while api_call_count < max_iterations:
    # 1. 调用 LLM
    response = await llm_call(messages)

    # 2. 检查是否有工具调用
    if tool_calls := response.tool_calls:
        # 3. 执行工具
        results = await execute_tools(tool_calls)

        # 4. 将结果追加到消息历史
        messages.append(tool_results)

        # 5. 继续循环，让模型处理工具结果
        api_call_count += 1
    else:
        # 没有工具调用，返回最终响应
        break
```

**AI Platform 当前状态：**

```python
# 仅支持单次 LLM 调用
async def stream(...):
    async for chunk in model_instance.invoke_llm(...):
        yield chunk  # 直接流式返回，无工具循环
```

**差距：** 完全缺失工具循环机制

---

## 三、数据模型对比

### 3.1 消息模型

#### Hermes SessionMessage

```typescript
interface SessionMessage {
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string | null
  reasoning?: string           // 推理过程
  reasoning_content?: string   // 推理内容
  tool_calls?: ToolCall[]      // 工具调用
  tool_call_id?: string        // 工具调用 ID
  tool_name?: string           // 工具名称
  timestamp?: number
  // ... 更多字段
}
```

#### AI Platform Message

```python
class Message(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole  # USER, ASSISTANT, SYSTEM
    content: str | None
    status: MessageStatus  # PENDING, COMPLETED, FAILED
    query: str | None
    answer: str | None
    token_count: int | None
    message_metadata: dict | None
```

**差距：**
- 缺少 `tool` 角色
- 缺少 `tool_calls` 字段
- 缺少 `reasoning` 字段
- 数据库模型不支持工具调用消息

### 3.2 消息部分 (Message Parts)

#### Hermes ChatMessagePart

```typescript
type ChatMessagePart =
  | TextPart
  | ReasoningPart
  | ToolCallPart
  | ToolResultPart
  | SourceUrlPart
  | SourceDocumentPart
  | FilePart
  | DataPart
```

#### AI Platform 当前状态

- 仅支持简单的 `content` 字符串
- 无结构化的消息部分

**差距：** 完全缺失消息部分机制

---

## 四、流式响应对比

### 4.1 Hermes 流事件

```python
# 结构化的流事件
MessageChunk(text="你好")      # 文本增量
MessageStop(final=False)       # 消息段结束
ToolCallChunk(tool_name="read_file")  # 工具调用开始
ToolCallFinish(tool_name="read_file") # 工具调用结束
```

**优点：**
- 类型安全
- 易于解析和处理
- 支持复杂的流式场景

### 4.2 AI Platform SSE

```python
# 简单的 SSE 流
async for chunk in llm_service.stream(...):
    yield f"data: {chunk.text}\n\n"
```

**缺点：**
- 缺少结构化信息
- 无法区分文本、工具调用、推理等不同类型
- 前端需要自行解析

---

## 五、改造方案

### 5.1 总体策略

```
Phase 1: 基础能力补齐（高优先级）
├── 工具循环机制
├── 流事件系统
└── 消息模型扩展

Phase 2: 核心功能增强（中优先级）
├── 对话中断
├── 对话压缩
└── 推理过程展示

Phase 3: 高级特性（低优先级）
├── 平台适配器
├── 消息分支
└── Steering 机制
```

### 5.2 Phase 1 详细设计

#### 5.2.1 工具循环实现

**新增文件：** `server/python/src/ai/services/conversation_loop.py`

```python
class ConversationLoop:
    """对话循环管理器"""

    def __init__(
        self,
        llm_service: LLMService,
        tool_executor: ToolExecutor,
        max_iterations: int = 10,
    ):
        self.llm_service = llm_service
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations

    async def run(
        self,
        messages: List[PromptMessage],
        tools: List[PromptMessageTool] | None = None,
        stream_callback: Callable[[StreamEvent], None] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """运行对话循环"""

        iteration = 0

        while iteration < self.max_iterations:
            # 1. 调用 LLM
            response = await self.llm_service.invoke(
                prompt_messages=messages,
                tools=tools,
                stream=True,
            )

            # 2. 处理流式响应
            tool_calls = []
            async for chunk in response:
                # 转换为流事件
                event = self._chunk_to_event(chunk)

                # 发送事件
                if stream_callback:
                    stream_callback(event)
                yield event

                # 收集工具调用
                if chunk.tool_calls:
                    tool_calls.extend(chunk.tool_calls)

            # 3. 检查是否有工具调用
            if not tool_calls:
                # 没有工具调用，返回最终响应
                yield MessageStop(final=True)
                break

            # 4. 执行工具
            for tc in tool_calls:
                yield ToolCallChunk(
                    tool_name=tc.function.name,
                    args=tc.function.arguments,
                )

                result = await self.tool_executor.execute(
                    tool_name=tc.function.name,
                    args=tc.function.arguments,
                )

                yield ToolCallFinish(
                    tool_name=tc.function.name,
                    result_preview=result[:100],
                )

                # 将工具结果添加到消息
                messages.append(ToolMessage(
                    content=result,
                    tool_call_id=tc.id,
                ))

            iteration += 1

        # 超过迭代限制
        if iteration >= self.max_iterations:
            yield ErrorEvent(message="达到最大迭代次数")
```

#### 5.2.2 流事件定义

**新增文件：** `server/python/src/ai/events/stream_events.py`

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass(frozen=True)
class MessageChunk:
    """文本增量块"""
    type: str = "message_chunk"
    text: str = ""

@dataclass(frozen=True)
class MessageStop:
    """消息结束"""
    type: str = "message_stop"
    final: bool = False

@dataclass(frozen=True)
class ToolCallChunk:
    """工具调用开始"""
    type: str = "tool_call_chunk"
    tool_name: str = ""
    tool_call_id: str = ""
    args: Optional[Dict[str, Any]] = None

@dataclass(frozen=True)
class ToolCallFinish:
    """工具调用结束"""
    type: str = "tool_call_finish"
    tool_name: str = ""
    tool_call_id: str = ""
    result_preview: Optional[str] = None
    is_error: bool = False

@dataclass(frozen=True)
class ReasoningChunk:
    """推理过程增量"""
    type: str = "reasoning_chunk"
    text: str = ""

@dataclass(frozen=True)
class ErrorEvent:
    """错误事件"""
    type: str = "error"
    message: str = ""

StreamEvent = (
    MessageChunk
    | MessageStop
    | ToolCallChunk
    | ToolCallFinish
    | ReasoningChunk
    | ErrorEvent
)
```

#### 5.2.3 消息模型扩展

**修改文件：** `server/python/src/ai/models/message.py`

```python
class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"  # 新增

class Message(BaseModel, ActiveRecordMixin, TenantMixin):
    """消息模型"""

    # ... 现有字段 ...

    # 新增字段
    tool_calls: Mapped[list | None] = mapped_column(
        postgresql.JSONB,
        nullable=True,
        comment="工具调用列表"
    )
    tool_call_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="工具调用 ID（tool 角色消息）"
    )
    reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="推理过程"
    )
```

#### 5.2.4 API 端点改造

**修改文件：** `server/python/src/ai/controllers/v1/chat/llm.py`

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """聊天接口（支持工具循环）"""

    async def event_stream():
        # 1. 获取或创建会话
        conversation, _ = await ConversationService.get_or_create(
            session=db,
            conversation_id=request.conversation_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
        )

        # 2. 获取消息历史
        messages = await Message.list_by_conversation(
            session=db,
            conversation_id=conversation.id,
        )

        # 3. 转换为 PromptMessage
        prompt_messages = to_prompt_messages(messages, request.message)

        # 4. 获取可用工具
        tools = await get_available_tools(
            tenant_id=request.tenant_id,
            app_id=conversation.app_id,
        )

        # 5. 运行对话循环
        loop = ConversationLoop(
            llm_service=LLMService(request.tenant_id),
            tool_executor=ToolExecutor(),
        )

        async for event in loop.run(
            messages=prompt_messages,
            tools=tools,
        ):
            # 序列化为 SSE 格式
            yield f"data: {event.to_json()}\n\n"

        # 6. 持久化消息
        # ... 保存用户消息和助手消息 ...

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )
```

### 5.3 前端改造

#### 5.3.1 流事件处理

**新增文件：** `web/vue/src/ai/composables/useStreamEvents.ts`

```typescript
import type { StreamEvent } from '@/ai/types/events'

export function useStreamEvents() {
  const messages = ref<Message[]>([])
  const currentMessage = ref<Message | null>(null)
  const isProcessing = ref(false)

  function handleEvent(event: StreamEvent) {
    switch (event.type) {
      case 'message_chunk':
        // 追加文本
        if (currentMessage.value) {
          currentMessage.value.content += event.text
        }
        break

      case 'tool_call_chunk':
        // 添加工具调用部分
        if (currentMessage.value) {
          currentMessage.value.parts.push({
            type: 'tool-call',
            toolName: event.tool_name,
            toolCallId: event.tool_call_id,
            args: event.args,
            status: 'running',
          })
        }
        break

      case 'tool_call_finish':
        // 更新工具调用状态
        if (currentMessage.value) {
          const part = currentMessage.value.parts.find(
            p => p.type === 'tool-call' && p.toolCallId === event.tool_call_id
          )
          if (part) {
            part.status = 'completed'
            part.result = event.result_preview
          }
        }
        break

      case 'message_stop':
        if (event.final && currentMessage.value) {
          messages.value.push(currentMessage.value)
          currentMessage.value = null
          isProcessing.value = false
        }
        break
    }
  }

  return {
    messages,
    currentMessage,
    isProcessing,
    handleEvent,
  }
}
```

#### 5.3.2 消息渲染组件

**新增文件：** `web/vue/src/ai/components/MessagePart.vue`

```vue
<template>
  <div class="message-part">
    <!-- 文本部分 -->
    <div v-if="part.type === 'text'" class="prose">
      {{ part.text }}
    </div>

    <!-- 工具调用部分 -->
    <div v-else-if="part.type === 'tool-call'" class="tool-call">
      <div class="tool-header">
        <span class="tool-name">{{ part.toolName }}</span>
        <Badge :variant="part.status === 'running' ? 'default' : 'success'">
          {{ part.status === 'running' ? '执行中...' : '已完成' }}
        </Badge>
      </div>
      <Collapsible v-if="part.args">
        <pre>{{ JSON.stringify(part.args, null, 2) }}</pre>
      </Collapsible>
      <div v-if="part.result" class="tool-result">
        <pre>{{ part.result }}</pre>
      </div>
    </div>

    <!-- 推理部分 -->
    <Collapsible v-else-if="part.type === 'reasoning'" title="推理过程">
      <div class="reasoning">
        {{ part.text }}
      </div>
    </Collapsible>
  </div>
</template>
```

---

## 六、改造工作量估算

### 6.1 后端改造

| 任务 | 文件数 | 预估工时 | 优先级 |
|------|-------|---------|--------|
| 流事件定义 | 1 | 4h | P0 |
| 工具循环实现 | 1 | 16h | P0 |
| 消息模型扩展 | 2 | 8h | P0 |
| 工具执行器 | 1 | 12h | P0 |
| API 端点改造 | 2 | 8h | P0 |
| 对话中断机制 | 2 | 12h | P1 |
| 对话压缩 | 2 | 16h | P1 |
| 推理过程支持 | 2 | 8h | P1 |
| **小计** | **13** | **84h** | |

### 6.2 前端改造

| 任务 | 文件数 | 预估工时 | 优先级 |
|------|-------|---------|--------|
| 流事件处理 Hook | 1 | 8h | P0 |
| 消息部分类型定义 | 1 | 4h | P0 |
| 消息部分渲染组件 | 3 | 16h | P0 |
| 聊天页面改造 | 1 | 12h | P0 |
| 工具调用 UI | 2 | 16h | P1 |
| 推理过程展示 | 2 | 8h | P1 |
| **小计** | **10** | **64h** | |

### 6.3 测试与文档

| 任务 | 预估工时 |
|------|---------|
| 单元测试 | 24h |
| 集成测试 | 16h |
| API 文档 | 8h |
| **小计** | **48h** |

### 6.4 总计

| 阶段 | 工时 | 人员 | 周期 |
|------|------|------|------|
| Phase 1 (P0) | 120h | 1 人 | 3 周 |
| Phase 2 (P1) | 76h | 1 人 | 2 周 |
| **总计** | **196h** | **1 人** | **5 周** |

---

## 七、风险评估

### 7.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 工具循环可能导致无限循环 | 高 | 实现严格的迭代限制和超时机制 |
| 流事件序列化性能 | 中 | 使用高效的序列化库，缓存常用事件 |
| 数据库模型迁移 | 中 | 编写迁移脚本，提供回滚方案 |
| 前端状态管理复杂度 | 中 | 使用 Pinia Store 管理状态，编写单元测试 |

### 7.2 兼容性风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 现有 API 客户端不兼容 | 高 | 提供新旧两个 API 版本，逐步迁移 |
| 消息模型变更影响现有数据 | 高 | 编写数据迁移脚本，提供降级方案 |
| 前端组件接口变更 | 中 | 使用 TypeScript 严格检查，逐步重构 |

---

## 八、实施建议

### 8.1 分阶段实施

```
Week 1-2: Phase 1 基础设施
├── 流事件定义
├── 消息模型扩展
└── 工具循环核心逻辑

Week 3: Phase 1 集成
├── API 端点改造
├── 前端流事件处理
└── 基础测试

Week 4-5: Phase 2 增强
├── 对话中断
├── 对话压缩
└── 推理过程

Week 6+: Phase 3 高级特性
├── 平台适配器
├── Steering
└── 消息分支
```

### 8.2 质量保证

1. **代码审查**：所有变更必须经过 Code Review
2. **单元测试**：核心逻辑测试覆盖率 > 80%
3. **集成测试**：编写端到端测试用例
4. **性能测试**：模拟高并发场景，验证流式响应性能
5. **文档更新**：同步更新 API 文档和开发指南

### 8.3 监控与告警

1. **流式响应延迟**：监控 SSE 连接时长
2. **工具执行耗时**：记录每个工具的执行时间
3. **迭代次数**：监控对话循环迭代次数分布
4. **错误率**：追踪各类错误的发生频率

---

## 九、总结

AI Platform 与 Hermes 在对话接口能力上存在显著差距，主要体现在：

1. **工具循环机制**：AI Platform 完全缺失，这是最关键的差距
2. **流事件系统**：AI Platform 的流式响应过于简单，无法支持复杂场景
3. **消息模型**：缺少对工具调用消息的支持

改造工作量约 **5 周**，建议分三个阶段实施：

- **Phase 1**（3 周）：补齐核心能力，实现工具循环和流事件系统
- **Phase 2**（2 周）：增强功能，支持对话中断、压缩和推理过程
- **Phase 3**（持续）：高级特性，逐步对齐 Hermes 的完整能力

改造完成后，AI Platform 将具备与 Hermes 相当的对话能力，能够支持复杂的工具调用场景和更好的用户体验。
