## 1. 前端依赖安装

- [x] 1.1 安装 AI SDK 核心依赖：`pnpm add ai @ai-sdk/vue`
- [x] 1.2 安装 ai-elements-vue 组件：`npx ai-elements-vue@latest`（选择 conversation、message、prompt-input、code-block 组件）
- [x] 1.3 验证依赖安装成功，项目可正常启动

## 2. 前端 AI 模块骨架

- [x] 2.1 创建模块目录结构：`web/vue/src/ai/`（api、composables、pages、router、stores、types）
- [x] 2.2 创建模块入口文件 `web/vue/src/ai/index.ts`，导出 ModuleDescriptor
- [x] 2.3 创建路由配置 `web/vue/src/ai/router/index.ts`
- [x] 2.4 创建类型定义 `web/vue/src/ai/types/index.ts`（AppUIMessage、AIChatRequest）
- [x] 2.5 修改 `web/vue/src/config/modules.ts`，添加 `ai` 到 ENABLED_MODULES

## 3. 前端 API 和状态管理

- [x] 3.1 创建会话 API：`web/vue/src/ai/api/conversation.ts`（复用 framework/api/client）
- [x] 3.2 创建会话 Store：`web/vue/src/ai/stores/conversation.ts`（会话列表、当前模型状态）
- [x] 3.3 创建 useChat composable：`web/vue/src/ai/composables/useChat.ts`（封装 @ai-sdk/vue useChat）

## 4. 前端对话页面

- [x] 4.1 创建 ChatPage：`web/vue/src/ai/pages/ChatPage.vue`
- [x] 4.2 组装 ai-elements 组件：Conversation、Message、PromptInput
- [x] 4.3 集成 useChat 实现消息发送和接收
- [x] 4.4 验证流式响应正确渲染（Markdown、代码高亮）

## 5. 后端 Schema 新增

- [ ] 5.1 创建 AI SDK 请求 Schema：`server/python/src/ai/schemas/chat.py`
  - `AIChatRequest`：id、messages、trigger、messageId、body
  - `UIMessage`：id、role、parts
  - `UIMessagePart`：type、text 等
  - `BodyConfig`：model、search、files（复用现有 ModelConfig 等）
- [ ] 5.2 标记 `LLMChatCompletion` 为 deprecated（添加注释）

## 6. 后端接口改造

- [ ] 6.1 修改 `chat_messages` 函数接收 `AIChatRequest`
- [ ] 6.2 实现消息提取逻辑：从 messages 最后一条的 parts 提取用户查询
- [ ] 6.3 修改 SSE 事件格式为 AI SDK UIMessageChunk 标准
  - `{"type":"start","messageId":"..."}`
  - `{"type":"text-start","id":"..."}`
  - `{"type":"text-delta","id":"...","delta":"..."}`
  - `{"type":"text-end","id":"..."}`
  - `{"type":"finish","finishReason":"stop","usage":{...}}`
  - `data: [DONE]`
- [ ] 6.4 修改 `run_llm_task` 事件处理逻辑
- [ ] 6.5 修改 `_sse_generator` 输出格式
- [ ] 6.6 更新响应 headers（移除 X-Task-ID 等非标准 header 或保留为扩展）

## 7. 前后端联调验证

- [ ] 7.1 启动后端服务：`uv run runserver`
- [ ] 7.2 启动前端服务：`pnpm dev`
- [ ] 7.3 验证发送消息成功，收到流式响应
- [ ] 7.4 验证会话创建和消息持久化
- [ ] 7.5 验证多租户数据隔离

## 8. 后端单元测试

- [ ] 8.1 创建 `tests/ai/schemas/test_chat.py`：测试 AIChatRequest 验证
- [ ] 8.2 创建 `tests/ai/controllers/v1/chat/test_llm.py`：测试接口请求处理

## 9. 前端单元测试

- [ ] 9.1 创建 `tests/ai/composables/useChat.test.ts`：测试 useChat 封装
- [ ] 9.2 创建 `tests/ai/stores/conversation.test.ts`：测试会话状态管理

---

## 阶段二任务（后续变更）

以下任务不在本次变更范围内，记录为后续迭代参考：

- 引入 `UIMessageChunkCallbackHandler` 替代直接修改 `run_llm_task`
- 工具调用可视化（tool、confirmation 组件）
- 会话管理页面（列表、切换、删除）
- 模型选择器组件（动态提供商/模型列表）
