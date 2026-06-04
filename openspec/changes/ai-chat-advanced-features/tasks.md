## 1. 后端重构 - UIMessageChunkCallbackHandler

- [x] 1.1 创建 `server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`
- [x] 1.2 实现 `on_chat_model_stream` 事件处理，输出 AI SDK text-delta 格式
- [x] 1.3 实现 `on_tool_start` 事件处理，输出 AI SDK tool-call 格式
- [x] 1.4 实现 `on_tool_end` 事件处理，输出 AI SDK tool-result 格式
- [x] 1.5 修改 `run_llm_task()` 使用 Callback Handler 替代直接事件处理
- [x] 1.6 编写单元测试验证 SSE 格式与阶段一一致

## 2. 工具调用可视化

- [x] 2.1 安装 ai-elements-vue tool 组件到 `web/vue/src/components/ai-elements/`
- [x] 2.2 修改 `ChatPage.vue` 集成 ToolCall 组件
- [x] 2.3 实现 tool-invocations 消息部分渲染
- [x] 2.4 添加工具调用状态样式（进行中、已完成、失败）
- [x] 2.5 实现工具结果折叠展示

## 3. 会话管理

- [x] 3.1 创建 `server/python/src/ai/controllers/v1/conversation.py`
- [x] 3.2 实现 `GET /api/v1/conversations` 接口返回会话列表
- [x] 3.3 实现 `DELETE /api/v1/conversations/{id}` 接口删除会话
- [x] 3.4 创建会话列表请求/响应 Schema
- [x] 3.5 创建前端页面 `web/vue/src/ai/pages/ConversationListPage.vue`
- [x] 3.6 实现会话列表展示和分页加载
- [x] 3.7 实现会话切换跳转到 ChatPage
- [x] 3.8 实现会话删除功能和确认弹窗
- [x] 3.9 配置路由 `/ai/conversations` 和菜单项

## 4. 模型选择器

- [x] 4.1 创建 `server/python/src/ai/controllers/v1/model.py`
- [x] 4.2 实现 `GET /api/v1/models` 接口返回提供商和模型列表
- [x] 4.3 创建模型列表响应 Schema
- [x] 4.4 创建前端组件 `web/vue/src/ai/components/ModelSelector.vue`
- [x] 4.5 实现提供商分组选择器 UI
- [x] 4.6 实现模型选择同步到 useChat body.model
- [x] 4.7 替换 ChatPage 中的静态模型选择器

## 5. 测试与验证

- [x] 5.1 后端单元测试：Callback Handler 事件格式
- [x] 5.2 后端集成测试：会话列表接口
- [x] 5.3 后端集成测试：模型列表接口
- [x] 5.4 前端组件测试：ModelSelector
- [x] 5.5 前端组件测试：ConversationListPage
- [ ] 5.6 E2E 测试：完整对话流程含工具调用（已提供 TEST_PLAN.md）
