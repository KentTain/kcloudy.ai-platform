## 为什么

阶段一（ai-chat-module）已完成基础对话功能，但存在技术债和缺失高级特性：
1. 后端直接修改 `run_llm_task()` 输出 SSE 格式，职责不清，难以扩展
2. 工具调用事件已支持但前端无可视化
3. 缺少会话管理页面，用户无法查看历史对话
4. 模型选择器使用静态配置，无法动态获取可用模型

## 变更内容

### 新增

- **UIMessageChunkCallbackHandler**：LangChain AsyncCallbackHandler 实现，职责分离
- **工具调用可视化**：前端 tool、confirmation 组件，展示工具执行状态
- **会话管理页面**：会话列表、切换、删除功能
- **模型选择器组件**：动态获取提供商和模型列表

### 修改

- **后端 `run_llm_task`**：移除直接 SSE 格式化逻辑，改用 Callback Handler
- **前端 ChatPage**：集成工具调用组件

### 依赖

- 依赖 `ai-chat-module` 变更已完成

## 功能 (Capabilities)

### 新增功能

- `tool-call-visualization`: 工具调用可视化功能，展示工具执行状态和结果
- `conversation-management`: 会话管理功能，支持列表、切换、删除会话
- `dynamic-model-selection`: 动态模型选择功能，从后端获取可用模型列表

### 修改功能

- `ai-chat`: 后端实现重构，引入 Callback Handler 替代直接修改
  - 阶段一的直接修改逻辑将被 Callback Handler 替代
  - 功能行为不变，仅实现方式改变

## 影响

### 前端

- 新增 `web/vue/src/ai/pages/ConversationListPage.vue`
- 新增 `web/vue/src/ai/components/ModelSelector.vue`
- 安装 ai-elements-vue 的 tool、confirmation 组件
- 修改 `web/vue/src/ai/pages/ChatPage.vue` 集成工具调用组件

### 后端

- 新增 `server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`
- 修改 `server/python/src/ai/controllers/v1/chat/llm.py` 使用 Callback Handler
- 新增 `server/python/src/ai/controllers/v1/conversation.py` 会话管理接口
- 新增 `server/python/src/ai/controllers/v1/model.py` 模型列表接口

### API

- `GET /api/v1/conversations`：获取会话列表
- `DELETE /api/v1/conversations/{id}`：删除会话
- `GET /api/v1/models`：获取可用模型列表

### 数据库

- 无变更（复用现有 `Conversation`、`Message` 模型）

### 兼容性

- 后端重构不影响前端，SSE 格式保持一致
- 新增接口为增量，不影响现有功能
