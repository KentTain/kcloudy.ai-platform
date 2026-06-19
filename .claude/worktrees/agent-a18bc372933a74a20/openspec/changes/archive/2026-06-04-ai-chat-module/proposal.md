## 为什么

前端需要实现类似 ChatGPT 的对话功能，但当前后端 `/chat-messages` 接口使用自定义 SSE 格式，与 Vercel AI SDK 标准协议不兼容。采用 AI SDK 标准协议可以：

1. 利用成熟的 `ai-elements-vue` 组件库快速构建对话界面
2. 标准化协议便于与生态系统集成（LangGraph、MCP 等）
3. 支持工具调用、思考过程展示等高级特性

## 变更内容

### 新增

- **前端 AI 模块**：`web/vue/src/ai/`，包含对话页面、会话管理、模型选择
- **ai-elements-vue 组件**：安装到 `web/vue/src/components/ai-elements/`，提供对话、消息、输入等组件
- **模型选择功能**：支持用户选择不同的模型提供商和模型名称

### 修改

- **后端 `/chat-messages` 接口**：请求格式从 `LLMChatCompletion` 改为 `AIChatRequest`（AI SDK 标准格式）
- **SSE 响应格式**：从 `{event, data}` 改为 AI SDK `UIMessageChunk` 标准格式

### 保留

- 现有 `LLMChatCompletion` Schema 标记为 deprecated 但保留
- Agent 层（`AlonChatModel`、`AgentFactory`）不变
- 会话持久化（`Conversation`、`Message` 模型）不变

## 功能 (Capabilities)

### 新增功能

- `ai-chat`: AI 对话功能，支持流式响应、会话管理、消息历史
- `model-selection`: 模型选择功能，支持用户选择不同的模型提供商和模型名称

### 修改功能

（无 - 现有接口无前端调用者，视为新增功能）

## 影响

### 前端

- 新增 `web/vue/src/ai/` 模块目录
- 新增 `web/vue/src/components/ai-elements/` 组件目录
- 修改 `web/vue/src/config/modules.ts` 启用 ai 模块
- 新增依赖：`ai`、`@ai-sdk/vue`

### 后端

- 修改 `server/python/src/ai/controllers/v1/chat/llm.py`
- 新增 `server/python/src/ai/schemas/chat.py`（AIChatRequest 等）
- 阶段二新增 `server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`

### API

- `POST /api/v1/chat-messages`：请求格式变更，响应格式变更

### 数据库

- 无变更（复用现有 `Conversation`、`Message` 模型）

### 兼容性

- 现有 `/chat-messages` 接口无前端调用者，可安全改造
- 旧 Schema 保留但不推荐使用
