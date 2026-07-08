# Hermes 对话接口架构分析

## 一、核心架构概览

### 1.1 主要组件

```
┌─────────────────────────────────────────────────────────────────┐
│                         Hermes 对话架构                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  Platform    │───▶│  Gateway/        │───▶│   AIAgent    │  │
│  │  Adapters    │    │  StreamEvents    │    │              │  │
│  │              │    │                  │    │              │  │
│  │ - Telegram   │    │ - MessageChunk   │    │ - run_conv() │  │
│  │ - Discord    │    │ - ToolCallChunk  │    │ - Tool Loop  │  │
│  │ - API Server │    │ - MessageStop    │    │ - Compression│  │
│  │ - iMessage   │    │ - Commentary     │    │ - Steering   │  │
│  └──────────────┘    └──────────────────┘    └──────────────┘  │
│         │                     │                      │           │
│         └─────────────────────┴──────────────────────┘           │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │  Conversation     │                        │
│                    │  Loop             │                        │
│                    │                   │                        │
│                    │ - Turn Context    │                        │
│                    │ - Tool Execution  │                        │
│                    │ - Message History │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 关键文件路径

| 组件 | 文件路径 | 职责 |
|------|---------|------|
| 对话循环 | `agent/conversation_loop.py` | 核心对话流程控制 |
| AI Agent | `run_agent.py` | Agent 实例，工具调用，状态管理 |
| 流事件 | `gateway/stream_events.py` | 结构化流事件定义 |
| 平台适配 | `gateway/platforms/base.py` | 平台抽象基类 |
| API 服务器 | `gateway/platforms/api_server.py` | HTTP API 适配器 |

---

## 二、流事件系统 (Stream Events)

### 2.1 设计理念

Hermes 的流事件系统采用了**关注点分离**的设计原则：

- **Agent 负责**：决定"发生了什么"（What happened）
- **Gateway 负责**：决定"如何交付"（How to deliver）

这种设计使得：
- Agent 不需要知道平台细节
- Gateway 可以根据平台能力优化展示
- 历史记录不会被展示层的决策污染

### 2.2 核心事件类型

```python
# 消息相关事件
@dataclass(frozen=True)
class MessageChunk:
    """流式文本增量块"""
    text: str

@dataclass(frozen=True)
class MessageStop:
    """消息段落结束"""
    final: bool = False

@dataclass(frozen=True)
class Commentary:
    """工具迭代间的完整中间消息"""
    text: str

# 工具调用事件
@dataclass(frozen=True)
class ToolCallChunk:
    """工具调用开始/状态变更"""
    tool_name: str
    preview: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    index: int = 0

@dataclass(frozen=True)
class ToolCallFinish:
    """工具调用完成"""
    tool_name: str
    result_preview: Optional[str] = None
    is_error: bool = False
    index: int = 0
```

### 2.3 事件流示例

```
User: "帮我分析这个项目的结构"

→ MessageChunk("好的")
→ MessageChunk("，我")
→ MessageChunk("来分析")
→ MessageStop(final=False)
→ ToolCallChunk(tool_name="list_files", index=0)
→ ToolCallFinish(tool_name="list_files", index=0)
→ MessageChunk("项目包含以下模块...")
→ MessageStop(final=True)
```

---

## 三、对话循环核心逻辑

### 3.1 run_conversation 函数签名

```python
def run_conversation(
    agent,
    user_message: str,
    system_message: str = None,
    conversation_history: List[Dict[str, Any]] = None,
    task_id: str = None,
    stream_callback: Optional[callable] = None,
    persist_user_message: Optional[str] = None,
    persist_user_timestamp: Optional[float] = None,
    moa_config: Optional[dict[str, Any]] = None,
) -> Dict[str, Any]:
```

### 3.2 对话流程

```
1. 构建回合上下文 (build_turn_context)
   ├── 安装安全 stdio
   ├── 净化用户消息
   ├── 恢复/构建系统提示词
   ├── 会话持久化准备
   └── 预取外部记忆

2. 主循环 (while api_call_count < max_iterations)
   ├── 检查中断请求
   ├── 消费迭代预算
   ├── 触发 step_callback
   ├── 排空待处理的 steering
   ├── 构建 API 消息
   ├── 调用 LLM API
   ├── 处理响应
   │   ├── 流式回调
   │   ├── 提取推理内容
   │   └── 解析工具调用
   ├── 执行工具调用
   │   ├── 并行执行
   │   └── 顺序执行
   ├── 应用工具结果
   └── 检查终止条件

3. 后处理
   ├── 持久化会话
   ├── 同步外部记忆
   └── 清理资源
```

### 3.3 关键特性

| 特性 | 说明 |
|------|------|
| **工具循环** | 支持多轮工具调用，直到模型返回最终响应 |
| **Steering** | 允许用户在对话过程中插入指导性文本 |
| **中断** | 支持用户中断正在进行的对话 |
| **压缩** | 自动压缩长对话历史以节省 token |
| **预算管理** | 迭代次数限制，防止无限循环 |
| **Checkpoint** | 可选的检查点机制，支持状态回滚 |

---

## 四、消息模型

### 4.1 SessionMessage 接口（TypeScript）

```typescript
export interface SessionMessage {
  id?: string
  content: string | null
  context?: unknown
  name?: string
  reasoning?: null | string
  reasoning_content?: null | string
  reasoning_details?: unknown
  role: 'assistant' | 'system' | 'tool' | 'user'
  text?: unknown
  timestamp?: number
  tool_call_id?: null | string
  tool_calls?: unknown
  tool_name?: string
}
```

### 4.2 ChatMessage 类型（前端）

```typescript
export type ChatMessage = {
  id: string
  role: SessionMessage['role']
  parts: ChatMessagePart[]
  timestamp?: number
  pending?: boolean
  error?: string
  branchGroupId?: string
  hidden?: boolean
  attachmentRefs?: string[]
}
```

### 4.3 消息部分类型 (ChatMessagePart)

```typescript
export type ChatMessagePart =
  | TextPart
  | ReasoningPart
  | ToolCallPart
  | ToolResultPart
  | SourceUrlPart
  | SourceDocumentPart
  | FilePart
  | DataPart
```

---

## 五、平台适配器系统

### 5.1 适配器架构

```python
class BasePlatformAdapter:
    """平台适配器基类"""

    # 核心能力标识
    supports_async_delivery: bool = True

    # 核心方法
    async def connect(self) -> bool
    async def disconnect(self) -> None
    async def send(self, message: Any) -> None
    async def handle_message(self, event: MessageEvent) -> None
```

### 5.2 MessageEvent 数据结构

```python
@dataclass
class MessageEvent:
    """平台消息标准化表示"""

    # 消息内容
    text: str
    message_type: MessageType = MessageType.TEXT

    # 来源信息
    platform: str = ""
    chat_id: str = ""
    chat_type: str = ""
    thread_id: Optional[str] = None
    user_id: str = ""
    user_name: Optional[str] = None

    # 元数据
    message_id: Optional[str] = None
    reply_to: Optional[str] = None
    timestamp: Optional[float] = None

    # 附件
    attachments: List[CachedMedia] = field(default_factory=list)
```

### 5.3 API Server 适配器

```python
class APIServerAdapter(BasePlatformAdapter):
    """HTTP API 适配器"""

    supports_async_delivery = False  # 无持久通道，不支持异步交付

    # 主要端点
    POST /api/chat           # 对话接口
    GET  /api/conversations  # 会话列表
    GET  /api/messages       # 消息历史
```

---

## 六、工具执行系统

### 6.1 工具调用流程

```
1. 模型返回 tool_calls
2. 解析工具调用参数
3. 权限检查（可选）
4. 执行工具
   ├── 并行执行（非交互工具）
   └── 顺序执行（交互工具）
5. 生成工具结果消息
6. 追加到消息历史
7. 继续对话循环
```

### 6.2 工具执行器

```python
def execute_tool_calls_parallel(
    agent,
    assistant_message,
    messages: list,
    effective_task_id: str
) -> None:
    """并行执行工具调用"""

def execute_tool_calls_sequential(
    agent,
    assistant_message,
    messages: list,
    effective_task_id: str
) -> None:
    """顺序执行工具调用"""
```

### 6.3 工具进度回调

```python
# 工具执行过程中的回调
tool_progress_callback(
    "tool.started", tool_name, preview, args
)
tool_progress_callback(
    "tool.completed", tool_name, None, None,
    duration=tool_duration, is_error=False, result=result
)
```

---

## 七、高级特性

### 7.1 Steering（对话引导）

```python
def steer(self, text: str) -> bool:
    """
    在对话过程中注入指导性文本

    文本会被附加到下一个工具结果中，
    使模型能够看到并响应这些指导。
    """
```

### 7.2 中断机制

```python
def interrupt(self, message: str = None) -> None:
    """
    中断当前对话循环

    设置中断标志，主循环会在下次迭代时检查并退出。
    """
```

### 7.3 对话压缩

```python
def conversation_history_after_compression(
    agent: Any,
    messages: list
) -> Optional[list]:
    """
    智能压缩对话历史

    - 保留关键上下文
    - 移除冗余信息
    - 符合模型 token 限制
    """
```

### 7.4 多代理编排 (MOA)

```python
# MoA 配置
moa_config: Optional[dict[str, Any]] = None

# MoA 循环
from agent.moa_loop import run_moa_turn
```

---

## 八、会话持久化

### 8.1 会话数据库

```python
# 会话存储
session_db = {
    "session_id": str,
    "messages": List[Dict],
    "metadata": Dict,
    "created_at": float,
    "updated_at": float,
}
```

### 8.2 消息持久化

```python
def _persist_session(
    self,
    messages: List[Dict],
    conversation_history: List[Dict] = None
):
    """持久化会话消息到数据库"""
```

---

## 九、错误处理与重试

### 9.1 API 错误处理

```python
def _extract_api_error_context(error: Exception) -> Dict[str, Any]:
    """提取 API 错误上下文"""

def _summarize_api_error(error: Exception) -> str:
    """生成用户友好的错误摘要"""
```

### 9.2 流式重试

```python
def _log_stream_retry(
    self,
    *,
    kind: str,
    error: BaseException,
    attempt: int,
    max_attempts: int,
    mid_tool_call: bool,
    diag: Optional[Dict[str, Any]] = None,
) -> None:
    """记录流式重试"""
```

---

## 十、性能优化

### 10.1 提示词缓存

```python
# Anthropic 提示词缓存
_anthropic_prompt_cache_policy(
    provider=provider,
    base_url=base_url,
    api_mode=api_mode,
    model=model,
)
```

### 10.2 推理缓存

```python
# 思考内容缓存
_thinking_pad_cache: Dict[Tuple, bool]
```

### 10.3 活动追踪

```python
def _touch_activity(self, desc: str) -> None:
    """更新活动时间戳，用于监控和诊断"""
```

---

## 十一、扩展点

### 11.1 插件钩子

```python
# 工具调用前钩子
pre_tool_call_block_message()

# 工具调用后钩子
invoke_hook("post_tool_call", tool_name=..., tool_call_id=...)
```

### 11.2 回调系统

```python
# 可配置的回调函数
tool_progress_callback: callable
tool_start_callback: callable
tool_complete_callback: callable
thinking_callback: callable
reasoning_callback: callable
clarify_callback: callable
stream_delta_callback: callable
interim_assistant_callback: callable
step_callback: callable
event_callback: Callable[[str, dict], None]
```

---

## 十二、总结

Hermes 的对话接口设计体现了以下核心优势：

1. **高度模块化**：各组件职责清晰，易于扩展和维护
2. **平台无关**：通过适配器模式支持多种平台
3. **类型安全**：使用 dataclass 和 TypeScript 接口确保类型安全
4. **流式优先**：结构化的流事件系统，支持增量渲染
5. **可观测性**：丰富的回调、钩子和日志机制
6. **容错性**：完善的错误处理、重试和中断机制
7. **性能优化**：缓存、压缩、并行执行等优化策略

这些设计使得 Hermes 能够处理复杂的对话场景，同时保持代码的可维护性和可扩展性。
