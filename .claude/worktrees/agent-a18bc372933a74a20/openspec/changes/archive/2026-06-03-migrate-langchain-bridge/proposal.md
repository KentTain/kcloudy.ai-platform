# LangChain 桥接层迁移提案

## 为什么

项目选择使用 LangChain 替代 Agno 作为 AI 框架，需要实现自定义 `AlonChatModel` 将 LangChain 的 `BaseChatModel` 桥接到平台的 `LLMService`。这样既可复用 LangChain 生态（Agent、Memory、Tools），又能保持与现有 Plugin 体系的兼容。

此变更依赖 `migrate-model-component` 完成后的 `LLMService`。

## 变更内容

实现 LangChain 自定义 ChatModel 桥接层：

- 新增 `AlonChatModel`：继承 `langchain_core.language_models.chat_models.BaseChatModel`
- 新增 `_agenerate()` 方法：桥接到 `LLMService.invoke()`
- 新增 `_astream()` 方法：桥接到 `LLMService.stream()`
- 新增消息类型转换器：`BaseMessage` ↔ `PromptMessage`
- 新增 Agent 工厂：简化 LangChain Agent / LangGraph 创建流程

**不包含**：知识库向量库桥接（本接口未使用）。

## 功能 (Capabilities)

### 新增功能

- `alon-chat-model`: LangChain 自定义 ChatModel，实现 `_agenerate` 和 `_astream` 方法，桥接到平台 LLMService
- `message-adapter`: 消息类型转换器，实现 LangChain BaseMessage 与平台 PromptMessage 的双向转换
- `agent-factory`: Agent 创建工厂，封装 LangChain AgentExecutor 和 LangGraph 的创建逻辑

### 修改功能

无（全新功能模块）。

## 影响

### 代码结构

```
extended/langchain/
├── models/
│   ├── alon_chat.py              # AlonChatModel 核心
│   └── message_adapter.py        # 消息类型转换
├── agents/
│   ├── agent_factory.py          # Agent 创建工厂
│   └── graph_builder.py          # LangGraph 构建器
└── __init__.py
```

### 依赖组件

| 组件 | 用途 | 状态 |
|------|------|------|
| `ai/components/model/services/llm_service.py` | LLM 调用服务 | ⏳ 依赖 migrate-model-component |
| `ai_plugin/sdk/entities/model/message.py` | PromptMessage 实体 | ✅ 已迁移 |
| `langchain-core` | BaseChatModel 基类 | ✅ 已安装 |
| `langgraph` | 工作流引擎 | ✅ 已安装 |

### API 端点

此变更不直接暴露 API 端点，为后续 `/chat-messages` 接口提供 LangChain 集成能力。

### 兼容性

- 无破坏性变更
- 新增模块，不影响现有功能
- 替代原 Agno 桥接方案
