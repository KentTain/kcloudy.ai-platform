# LangChain 桥接层技术设计

## 上下文

### 背景

项目选择使用 LangChain 替代 Agno 作为 AI 框架。LangChain 提供丰富的生态（Agent、Memory、Tools、LangGraph 工作流），但需要桥接到平台现有的 `LLMService` 才能复用 Plugin 体系的模型调用能力。

### 当前状态

```
已有组件：
├── ai_plugin/sdk/entities/model/message.py   # PromptMessage 实体
├── ai_plugin/sdk/entities/model/llm.py       # LLMResult, LLMResultChunk
├── ai/components/model/services/llm_service.py  # LLMService (待迁移)
├── langchain-core                            # BaseChatModel 基类
└── langgraph                                 # 工作流引擎

缺失组件：
└── ai/extended/langchain/                    # LangChain 桥接层 ← 本次实现
```

### 约束

1. 必须继承 `langchain_core.language_models.chat_models.BaseChatModel`
2. 必须实现 `_agenerate()` 和 `_astream()` 异步方法
3. 必须复用 `LLMService` 而非直接调用 `ModelClient`
4. 消息类型转换必须支持双向转换

## 目标 / 非目标

**目标：**

1. 实现 `AlonChatModel` 桥接 LangChain → LLMService
2. 实现消息类型双向转换器（BaseMessage ↔ PromptMessage）
3. 提供 Agent 创建工厂，简化 LangChain Agent/LangGraph 使用
4. 支持流式和非流式两种调用模式

**非目标：**

1. 知识库向量库桥接（本接口未使用）
2. 自定义 Tool 实现（使用 LangChain 内置工具）
3. Embedding/Rerank 模型桥接（本接口未使用）

## 决策

### 决策 1：继承 BaseChatModel

**选择**：继承 `langchain_core.language_models.chat_models.BaseChatModel`

**理由**：
- BaseChatModel 是 LangChain 的标准 Chat 模型接口
- 支持与 LangChain Agent、LangGraph 无缝集成
- 自动获得 `invoke`、`stream`、`batch` 等方法

**替代方案**：
- 继承 `SimpleChatModel`：功能受限，不支持高级特性
- 实现 `Runnable` 接口：需要手动实现更多方法

### 决策 2：消息类型转换策略

**选择**：独立的 `MessageAdapter` 类处理转换

**理由**：
- 单一职责：转换逻辑独立，易于测试和维护
- 双向转换：支持 LangChain → Platform 和 Platform → LangChain
- 可扩展：未来支持更多消息类型（Tool、Function 等）

**转换映射**：

```
LangChain                    Platform (ai_plugin)
─────────────────────────────────────────────────
HumanMessage          →     UserPromptMessage
AIMessage             →     AssistantPromptMessage
SystemMessage         →     SystemPromptMessage
ToolMessage           →     ToolPromptMessage (可选)
```

### 决策 3：流式响应处理

**选择**：直接透传 `LLMService.stream()` 的 `AsyncIterator[LLMResultChunk]`

**理由**：
- `LLMService.stream()` 已返回标准化的流式响应
- 转换为 `ChatGenerationChunk` 只需提取 `content` 字段
- 保持职责清晰，避免重复处理

**数据流**：

```
LLMService.stream()
    ↓ AsyncIterator[LLMResultChunk]
AlonChatModel._astream()
    ↓ AsyncIterator[ChatGenerationChunk]
LangChain Agent.astream_events()
    ↓ 标准事件流
```

### 决策 4：Agent 创建方式

**选择**：同时支持 AgentExecutor 和 LangGraph

**理由**：
- AgentExecutor：简单场景，快速上手
- LangGraph：复杂场景，支持状态管理、中断恢复
- 项目已有 LangGraph 使用经验（`demo/examples/langgraph_workflows/`）

**工厂方法**：

```python
# 简单场景
agent = AgentFactory.create_executor(model, tools, memory)

# 复杂场景
graph = AgentFactory.create_graph(model, tools, checkpointer)
```

## 风险 / 权衡

### 风险 1：LangChain 版本兼容性

**风险**：LangChain 更新频繁，API 可能变化

**缓解措施**：
- 锁定 `langchain[community]==1.3.0`
- 使用稳定的 `BaseChatModel` 接口
- 升级前在测试环境验证

### 风险 2：消息类型不完整

**风险**：LangChain 和 Platform 消息类型不完全对应

**缓解措施**：
- 首批支持 Human/AI/System 三种核心类型
- Tool/Function 消息后续按需扩展
- 不支持的消息类型抛出 `UnsupportedMessageTypeError`

### 风险 3：流式中断处理

**风险**：消费者提前退出导致资源泄漏

**缓解措施**：
- 使用 `async with` 上下文管理资源
- 确保 `finally` 块清理连接
- 记录完整的 usage 统计

## 迁移计划

### 阶段 1：消息转换器（约 1 小时）

1. 创建 `ai/extended/langchain/models/message_adapter.py`
2. 实现 `to_platform_message()` 方法
3. 实现 `to_langchain_message()` 方法
4. 编写单元测试

### 阶段 2：AlonChatModel（约 2-3 小时）

1. 创建 `ai/extended/langchain/models/alon_chat.py`
2. 实现 `_agenerate()` 非流式方法
3. 实现 `_astream()` 流式方法
4. 实现 `_llm_type` 和 `_identifying_params` 属性
5. 编写单元测试

### 阶段 3：Agent 工厂（约 2 小时）

1. 创建 `ai/extended/langchain/agents/agent_factory.py`
2. 实现 `create_executor()` 方法
3. 实现 `create_graph()` 方法（可选）
4. 编写使用示例

### 回滚策略

- 新增模块，不修改现有代码，可直接删除回滚
- 不涉及数据库变更
