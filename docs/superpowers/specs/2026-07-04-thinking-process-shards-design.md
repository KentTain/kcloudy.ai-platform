# AI 对话思考过程分片功能设计

**日期**: 2026-07-04
**状态**: 设计完成
**作者**: Claude Code Agent

## 1. 功能概述

为 AI 对话系统添加思考过程分片功能，通过 LangChain Callback 机制捕获 Agent 的完整推理链，以流式 SSE 事件实时推送到前端，并通过可折叠 UI 展示 AI 的思考过程。

### 1.1 核心目标

- **透明性**：让用户看到 AI 的推理过程，增强信任感
- **可调试**：帮助开发者理解 Agent 决策逻辑
- **通用性**：支持所有 LangChain 模型和 Agent
- **安全性**：防止敏感信息泄露

### 1.2 功能范围

| 支持范围 | 不支持范围 |
|---------|-----------|
| 所有 LangChain Agent | 非 LangChain 的 LLM 调用 |
| 完整推理链捕获 | 第三方服务内部推理 |
| 流式实时展示 | 思考过程持久化存储 |
| 可折叠 UI 展示 | 思考过程编辑功能 |

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 Layer                            │
│  Message.vue → ThinkingBlock.vue → ChainOfThought.vue       │
│       ↓                                                       │
│  useChat.ts → 处理 thinking-delta 事件                        │
└─────────────────────────────────────────────────────────────┘
                              ↓ SSE Stream
┌─────────────────────────────────────────────────────────────┐
│                        后端 Layer                             │
│  chat_messages() → SSE Generator → Event Queue               │
│       ↓                                                       │
│  UIMessageChunkCallbackHandler (扩展)                         │
│   ├─ on_chain_start/end (推理步骤跟踪)                        │
│   ├─ on_llm_start/end (LLM 思考跟踪)                          │
│   └─ on_tool_start/end (工具调用跟踪)                         │
│       ↓                                                       │
│  ReasoningStepBuilder (新增)                                  │
│   ├─ 构建推理树结构                                            │
│   ├─ 过滤敏感信息                                              │
│   └─ 生成 thinking-delta 事件                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件职责

| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **ReasoningStepBuilder** | 构建推理步骤 | LangChain 回调事件 | `thinking-delta` 事件 |
| **UIMessageChunkCallbackHandler** | 统一事件处理器 | 回调钩子 | SSE 事件队列 |
| **EventType 枚举** | 事件类型定义 | - | `thinking-start/delta/end` |
| **前端 ThinkingPart** | 思考内容展示 | `thinking-delta` | 可折叠 UI 组件 |

### 2.3 数据流

```
1. Agent 执行流程
   ↓
2. Callback 触发 (on_chain_start, on_llm_start, ...)
   ↓
3. ReasoningStepBuilder 构建推理步骤
   ↓
4. 生成 thinking-delta 事件 → Event Queue
   ↓
5. SSE Generator 流式发送
   ↓
6. 前端 useChat 接收并更新 UI
```

## 3. 数据模型

### 3.1 后端事件类型

```python
# server/python/src/ai/controllers/v1/chat/event_types.py

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

    # 新增：思考过程事件
    THINKING_START = "thinking-start"
    THINKING_DELTA = "thinking-delta"
    THINKING_END = "thinking-end"
```

### 3.2 思考事件数据结构

#### 思考开始事件

```json
{
  "type": "thinking-start",
  "id": "thinking-abc123",
  "title": "分析用户问题",
  "stepType": "reasoning"
}
```

#### 思考增量事件

```json
{
  "type": "thinking-delta",
  "id": "thinking-abc123",
  "delta": "用户想了解天气情况..."
}
```

#### 思考结束事件

```json
{
  "type": "thinking-end",
  "id": "thinking-abc123"
}
```

### 3.3 推理步骤类型

```python
class ReasoningStepType(str, Enum):
    """推理步骤类型"""

    REASONING = "reasoning"              # 推理分析
    DECISION = "decision"                # 决策制定
    TOOL_SELECTION = "tool_selection"    # 工具选择
    TOOL_EXECUTION = "tool_execution"    # 工具执行
    RESULT_ANALYSIS = "result_analysis"  # 结果分析
    ERROR_HANDLING = "error_handling"    # 错误处理
```

### 3.4 前端类型定义

```typescript
// web/vue/src/ai/types/index.ts

export type UIMessagePartType =
  | "thinking"        // 新增：思考过程
  | "text"
  | "image"
  | "tool-call"
  | "tool-result";

export interface ThinkingPart extends UIMessagePartBase {
  type: "thinking";
  thinking: string;              // 思考内容
  title?: string;                // 步骤标题
  stepType?: ReasoningStepType;  // 步骤类型
}

export type ReasoningStepType =
  | "reasoning"
  | "decision"
  | "tool_selection"
  | "tool_execution"
  | "result_analysis"
  | "error_handling";

export type UIMessagePart =
  | ThinkingPart    // 新增
  | TextPart
  | ImagePart
  | ToolCallPart
  | ToolResultPart;
```

### 3.5 SSE 事件流示例

```
data: {"type":"start","messageId":"msg-123"}

data: {"type":"thinking-start","id":"thinking-abc","title":"分析问题","stepType":"reasoning"}

data: {"type":"thinking-delta","id":"thinking-abc","delta":"用户想要查询天气..."}

data: {"type":"thinking-delta","id":"thinking-abc","delta":"需要使用天气工具..."}

data: {"type":"thinking-end","id":"thinking-abc"}

data: {"type":"tool-call","toolCallId":"tool-1","toolName":"get_weather","args":{...}}

data: {"type":"tool-result","toolCallId":"tool-1","result":"北京今天晴，25°C"}

data: {"type":"thinking-start","id":"thinking-def","title":"整合结果","stepType":"result_analysis"}

data: {"type":"thinking-delta","id":"thinking-def","delta":"根据查询结果..."}

data: {"type":"thinking-end","id":"thinking-def"}

data: {"type":"text-start","id":"text-xyz"}

data: {"type":"text-delta","id":"text-xyz","delta":"北京今天天气晴朗..."}

data: {"type":"text-end","id":"text-xyz"}

data: {"type":"finish","finishReason":"stop","usage":{...}}

data: [DONE]
```

## 4. 核心实现

### 4.1 ReasoningStepBuilder

**文件**: `server/python/src/extended/langchain/callbacks/reasoning_step_builder.py`

**职责**：
- 跟踪 LangChain 执行流程中的推理步骤
- 构建推理树结构（支持嵌套推理）
- 过滤敏感信息
- 生成符合 AI SDK 标准的 thinking-delta 事件

**关键方法**：

```python
class ReasoningStepBuilder:
    async def start_reasoning_step(
        self,
        step_type: ReasoningStepType,
        title: str | None = None,
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """开始一个新的推理步骤"""

    async def append_reasoning_content(self, content: str) -> None:
        """向当前活跃的推理步骤追加内容"""

    async def end_reasoning_step(self, step_id: str | None = None) -> None:
        """结束推理步骤"""
```

**关键特性**：
- 使用栈结构跟踪嵌套推理步骤
- 三层敏感信息过滤（关键词、正则、JSON 字段）
- 批量发送优化（减少网络开销）

### 4.2 UIMessageChunkCallbackHandler 扩展

**文件**: `server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`

**扩展方法**：

```python
async def on_chain_start(self, serialized, inputs, run_id, ...):
    """捕获 Agent 决策步骤"""

async def on_chain_end(self, outputs, run_id, ...):
    """结束决策步骤"""

async def on_llm_start(self, serialized, prompts, run_id, ...):
    """捕获 LLM 推理过程（非第一次调用）"""

async def on_llm_end(self, response, run_id, ...):
    """结束 LLM 推理步骤"""
```

**判断逻辑**：
- 第一次 LLM 调用：生成正文内容
- 后续 LLM 调用：工具调用后的分析（创建推理步骤）

### 4.3 SSE Generator 扩展

**文件**: `server/python/src/ai/controllers/v1/chat/llm.py`

**修改点**：

```python
async def _sse_generator(...):
    # 新增：跟踪思考块状态
    thinking_started = False

    # 处理思考过程事件
    if event_type == EventType.THINKING_START:
        yield _format_sse_line(event)
        thinking_started = True
    elif event_type == EventType.THINKING_DELTA:
        yield _format_sse_line(event)
    elif event_type == EventType.THINKING_END:
        yield _format_sse_line(event)
        thinking_started = False

    # 在 FINISH 事件中确保所有块已关闭
    if thinking_started:
        yield _format_sse_line({"type": EventType.THINKING_END, ...})
```

### 4.4 前端 ThinkingBlock 组件

**文件**: `web/vue/src/components/ai-elements/message/ThinkingBlock.vue`

**功能**：
- 可折叠展示思考过程
- 显示步骤类型标签（决策、推理、工具选择等）
- 支持多个思考块合并展示

**关键特性**：
- 使用 `Collapsible` 组件实现折叠
- 步骤类型颜色编码
- 默认折叠，点击展开

### 4.5 useChat 扩展

**文件**: `web/vue/src/ai/composables/useChat.ts`

**新增处理逻辑**：

```typescript
function processThinkingEvents(messages: UIMessage[]): UIMessage[] {
  return messages.map(message => {
    // 按 ID 分组合并思考块
    // 过滤无效内容
    // 限制内容长度
    // 重新组织 parts：思考在前，正文在后
  });
}
```

## 5. 错误处理

### 5.1 后端错误处理

| 场景 | 处理策略 |
|------|----------|
| 推理嵌套过深 | 限制最大深度为 10 层，超过则跳过 |
| 敏感信息泄露 | 三层过滤：关键词 + 正则 + JSON 字段 |
| 内容过长 | 后端限制单个思考块 10k 字符 |
| 事件发送失败 | 记录日志，不影响主流程 |
| Callback 异常 | 捕获异常，静默失败 |

### 5.2 前端错误处理

| 场景 | 处理策略 |
|------|----------|
| 无效的 parts 结构 | 记录警告，返回原始消息 |
| thinking-delta 乱序 | 使用 ID 关联，队列缓冲 |
| 内容过长 | 前端截断至 10k 字符 |
| 网络中断 | 30s 超时自动关闭思考块 |
| JSON 解析失败 | 跳过错误事件 |

### 5.3 敏感信息过滤实现

```python
def _filter_sensitive_info(self, content: str) -> str:
    """过滤敏感信息（三层检测）"""

    # 1. 关键词过滤
    for keyword in self.sensitive_keywords:
        if keyword in content.lower():
            return ""

    # 2. 正则匹配 API Key 格式
    api_key_pattern = re.compile(r'sk-[a-zA-Z0-9]{48}')
    if api_key_pattern.search(content):
        return ""

    # 3. JSON 字段检测
    try:
        if '{' in content and '}' in content:
            potential_json = content[content.index('{'):content.rindex('}')+1]
            data = json.loads(potential_json)

            sensitive_fields = ['api_key', 'password', 'token', 'secret']
            for field in sensitive_fields:
                if field in data:
                    return ""
    except:
        pass

    return content
```

## 6. 性能优化

### 6.1 批量发送机制

```python
# ReasoningStepBuilder 批量发送优化
self._pending_deltas: list[str] = []
self._batch_size = 5
self._batch_interval = 0.1  # 100ms

async def append_reasoning_content(self, content: str) -> None:
    self._pending_deltas.append(filtered_content)

    should_send = (
        len(self._pending_deltas) >= self._batch_size or
        time.time() - self._last_send_time >= self._batch_interval
    )

    if should_send:
        combined_delta = ''.join(self._pending_deltas)
        # 发送合并后的事件
```

### 6.2 性能控制参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| MAX_REASONING_DEPTH | 10 | 最大推理嵌套深度 |
| MAX_THINKING_LENGTH | 10000 | 单个思考块最大字符数 |
| BATCH_SIZE | 5 | 批量发送 delta 数量 |
| BATCH_INTERVAL | 0.1s | 批量发送间隔 |

## 7. 配置选项

### 7.1 ThinkingFeatureConfig

```python
@dataclass
class ThinkingFeatureConfig:
    """思考过程功能配置"""

    enabled: bool = True                          # 是否启用
    max_reasoning_depth: int = 10                 # 最大推理深度
    filter_level: str = "strict"                  # 过滤级别: off/basic/strict
    capture_tool_reasoning: bool = True           # 捕获工具调用推理
    batch_deltas: bool = True                     # 批量发送
    batch_size: int = 5                           # 批量大小
    batch_interval: float = 0.1                   # 批量间隔
    max_thinking_length: int = 10000              # 最大长度
```

### 7.2 使用方式

```python
# 在请求中传递配置
thinking_config = ThinkingFeatureConfig(
    enabled=chat_request.body.model.completion_params.get("enable_thinking", True),
    filter_level="strict",
)

callback_handler = UIMessageChunkCallbackHandler(
    event_queue,
    message_id,
    thinking_config=thinking_config,
)
```

## 8. 监控与日志

### 8.1 关键日志事件

```python
# 开始推理步骤
_logger.info(
    "reasoning_step_started",
    step_id=step_id,
    step_type=step_type.value,
    title=title,
    stack_depth=len(self.step_stack),
)

# 结束推理步骤
_logger.info(
    "reasoning_step_completed",
    step_id=current_step.id,
    content_length=len(current_step.content),
    duration_ms=(time.time() - start_time) * 1000,
)

# 敏感信息检测
_logger.warning(f"检测到敏感关键词: {keyword}")
```

### 8.2 监控指标

| 指标 | 说明 |
|------|------|
| reasoning_step_count | 推理步骤总数 |
| reasoning_depth_avg | 平均推理深度 |
| thinking_content_length | 思考内容长度 |
| sensitive_filter_count | 敏感信息过滤次数 |
| thinking_event_latency | 思考事件延迟 |

## 9. 测试策略

### 9.1 单元测试

**后端**：
- `test_reasoning_step_builder.py`：ReasoningStepBuilder 核心逻辑测试
- `test_ui_message_chunk_callback.py`：CallbackHandler 扩展测试
- 覆盖率目标：≥ 85%

**前端**：
- `ThinkingBlock.test.ts`：组件渲染和交互测试
- `useChat.test.ts`：思考事件处理测试
- 覆盖率目标：≥ 75%

### 9.2 集成测试

- 测试完整的 SSE 事件流
- 验证思考事件的正确顺序
- 验证嵌套推理步骤
- 覆盖关键用户路径

### 9.3 E2E 测试

- 用户发送需要推理的问题
- 验证思考过程块正确显示
- 验证折叠/展开交互
- 验证步骤类型标签显示

## 10. 文件清单

### 10.1 新增文件

**后端**：
- `server/python/src/extended/langchain/callbacks/reasoning_step_builder.py`
- `server/python/src/extended/langchain/callbacks/reasoning_types.py`
- `server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py`

**前端**：
- `web/vue/src/components/ai-elements/message/ThinkingBlock.vue`
- `web/vue/tests/ai/unit/components/ThinkingBlock.test.ts`

### 10.2 修改文件

**后端**：
- `server/python/src/ai/controllers/v1/chat/event_types.py` - 新增事件类型
- `server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py` - 扩展回调
- `server/python/src/ai/controllers/v1/chat/llm.py` - SSE Generator 扩展
- `server/python/tests/extended/langchain/callbacks/test_ui_message_chunk_callback.py` - 新增测试

**前端**：
- `web/vue/src/ai/types/index.ts` - 新增 ThinkingPart 类型
- `web/vue/src/ai/composables/useChat.ts` - 处理思考事件
- `web/vue/src/components/ai-elements/message/Message.vue` - 集成 ThinkingBlock

## 11. UI 效果

### 11.1 折叠状态

```
┌────────────────────────────────────────┐
│ 🧠 思考过程                    [决策]   │
└────────────────────────────────────────┘
```

### 11.2 展开状态

```
┌────────────────────────────────────────┐
│ 🧠 思考过程                    [决策] ▼ │
│ ─────────────────────────────────────  │
│                                        │
│ 分析问题                               │
│ 用户想了解北京天气，需要调用天气工具    │
│                                        │
│ ─────────────────────────────────────  │
│                                        │
│ 工具选择                               │
│ 选择 get_weather 工具，参数: 北京       │
│                                        │
│ ─────────────────────────────────────  │
│                                        │
│ 结果分析                               │
│ 工具返回晴天25°C，可以生成回复         │
└────────────────────────────────────────┘

北京今天天气晴朗，气温25°C...
```

### 11.3 步骤类型颜色编码

| 步骤类型 | 颜色 | 标签 |
|---------|------|------|
| reasoning | 蓝色 | 推理 |
| decision | 紫色 | 决策 |
| tool_selection | 橙色 | 工具选择 |
| tool_execution | 绿色 | 工具执行 |
| result_analysis | 青色 | 结果分析 |
| error_handling | 红色 | 错误处理 |

## 12. 风险与缓解

| 风险 | 影响 | 缓解措施 | 优先级 |
|------|------|----------|--------|
| 敏感信息泄露 | 高 | 三层过滤机制 + 严格模式 | P0 |
| 性能影响 | 中 | 批量发送 + 深度限制 + 异步处理 | P1 |
| 推理嵌套过深 | 中 | 最大深度限制为 10 层 | P1 |
| 前端内存溢出 | 中 | 内容长度限制 10k 字符 | P2 |
| 事件乱序 | 低 | ID 关联 + 状态管理 | P2 |

## 13. 实施计划

### 13.1 实施阶段

**阶段一：后端核心实现**（预计 2 天）
1. 实现 ReasoningStepBuilder
2. 扩展 UIMessageChunkCallbackHandler
3. 修改 SSE Generator
4. 编写单元测试

**阶段二：前端实现**（预计 1.5 天）
1. 定义 ThinkingPart 类型
2. 实现 ThinkingBlock 组件
3. 扩展 useChat 处理逻辑
4. 编写组件测试

**阶段三：集成测试**（预计 0.5 天）
1. 编写集成测试
2. 编写 E2E 测试
3. 性能测试

**阶段四：优化与文档**（预计 0.5 天）
1. 性能优化
2. 编写使用文档
3. 代码审查

### 13.2 验收标准

- [ ] 所有单元测试通过（覆盖率 ≥ 80%）
- [ ] 集成测试通过
- [ ] E2E 测试通过
- [ ] 敏感信息过滤有效
- [ ] 性能无明显下降
- [ ] UI 展示正确
- [ ] 代码审查通过

## 14. 未来扩展

### 14.1 短期扩展（1-2 个月）

- 思考过程持久化存储
- 思考过程搜索功能
- 思考过程导出功能

### 14.2 长期扩展（3-6 个月）

- 思考过程编辑功能
- 思考过程分享功能
- 思考过程可视化（思维导图）
- 支持自定义推理步骤类型

## 15. 参考资料

- [LangChain Callbacks Documentation](https://python.langchain.com/docs/modules/callbacks/)
- [Vercel AI SDK Streaming Protocol](https://sdk.vercel.ai/docs/ai-sdk-ui/streaming)
- [AI Platform Architecture](../../server/python/CLAUDE.md)
- [Vue 前端开发指南](../../web/vue/src/CLAUDE.md)

---

**批准状态**: ✅ 已批准
**下一步**: 创建实施计划
