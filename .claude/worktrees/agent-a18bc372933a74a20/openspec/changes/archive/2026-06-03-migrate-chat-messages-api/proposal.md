# LLM 对话接口迁移提案

## 为什么

完成所有前置变更后，需要实现 `/chat-messages` 接口本体，整合 LLMService、AlonChatModel、LangGraph Agent、会话持久化和任务管控，提供完整的流式对话能力。

这是整个迁移方案的最终集成步骤。

## 变更内容

实现 LLM 对话接口完整功能：

- 新增 `POST /api/v1/chat-messages` 接口：流式对话，返回 SSE 响应
- 新增 `POST /api/v1/chat-messages/:id/stop` 接口：停止正在进行的对话
- 新增请求 Schema：`LLMChatCompletion`、`ModelConfig`、`SearchConfig`
- 新增响应 Schema：SSE 事件格式（message/finish/error）
- 集成 LangGraph Agent 构建对话流程
- 集成会话创建/恢复逻辑
- 集成任务停止和超时清理

**不包含**：会话管理接口（列表、删除等）单独实现。

## 功能 (Capabilities)

### 新增功能

- `chat-messages-api`: LLM 对话接口，支持流式响应（SSE）、会话创建/恢复、联网搜索（可选）、任务停止
- `chat-sse-events`: SSE 事件格式定义，包含 message/finish/search_keywords/error 四种事件类型

### 修改功能

无（全新功能模块）。

## 影响

### 代码结构

```
ai/controllers/
└── v1/chat/
    └── llm.py                    # chat_messages, stop_chat_messages

ai/schemas/
└── completion.py                 # LLMChatCompletion, ModelConfig, SearchConfig
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat-messages` | 创建/恢复会话并发起对话 |
| POST | `/api/v1/chat-messages/:id/stop` | 停止指定会话的对话 |

### 依赖组件

| 组件 | 用途 | 状态 |
|------|------|------|
| `ai/components/model/services/llm_service.py` | LLM 调用 | ⏳ 依赖 migrate-model-component |
| `ai/extended/langchain/models/alon_chat.py` | LangChat 桥接 | ⏳ 依赖 migrate-langchain-bridge |
| `ai/extended/langchain/agents/agent_factory.py` | Agent 创建 | ⏳ 依赖 migrate-langchain-bridge |
| `ai/models/conversation.py` | 会话持久化 | ⏳ 依赖 migrate-conversation-persistence |
| `ai/services/memory_task/` | 任务管控 | ⏳ 依赖 migrate-conversation-persistence |

### SSE 事件格式

```
event: message
data: {"content": "你好"}

event: finish
data: {"prompt_tokens": 10, "completion_tokens": 20}

event: search_keywords
data: {"keywords": ["关键词1", "关键词2"]}

event: error
data: {"code": "MODEL_ERROR", "message": "模型调用失败"}
```

### 兼容性

- 无破坏性变更
- 新增 API 端点
- 与 Alon 平台 SSE 格式保持兼容
