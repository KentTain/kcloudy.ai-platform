## 1. 后端重构 - UIMessageChunkCallbackHandler

- [ ] 1.1 创建 `server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`
- [ ] 1.2 实现 `on_chat_model_stream` 事件处理，输出 AI SDK text-delta 格式
- [ ] 1.3 实现 `on_tool_start` 事件处理，输出 AI SDK tool-call 格式
- [ ] 1.4 实现 `on_tool_end` 事件处理，输出 AI SDK tool-result 格式
- [ ] 1.5 修改 `run_llm_task()` 使用 Callback Handler 替代直接事件处理
- [ ] 1.6 编写单元测试验证 SSE 格式与阶段一一致

## 2. 工具调用可视化

- [ ] 2.1 安装 ai-elements-vue tool 组件到 `web/vue/src/components/ai-elements/`
- [ ] 2.2 修改 `ChatPage.vue` 集成 ToolCall 组件
- [ ] 2.3 实现 tool-invocations 消息部分渲染
- [ ] 2.4 添加工具调用状态样式（进行中、已完成、失败）
- [ ] 2.5 实现工具结果折叠展示

## 3. 会话管理

- [ ] 3.1 创建 `server/python/src/ai/controllers/v1/conversation.py`
- [ ] 3.2 实现 `GET /api/v1/conversations` 接口返回会话列表
- [ ] 3.3 实现 `DELETE /api/v1/conversations/{id}` 接口删除会话
- [ ] 3.4 创建会话列表请求/响应 Schema
- [ ] 3.5 创建前端页面 `web/vue/src/ai/pages/ConversationListPage.vue`
- [ ] 3.6 实现会话列表展示和分页加载
- [ ] 3.7 实现会话切换跳转到 ChatPage
- [ ] 3.8 实现会话删除功能和确认弹窗
- [ ] 3.9 配置路由 `/ai/conversations` 和菜单项

## 4. 模型选择器

- [ ] 4.1 创建 `server/python/src/ai/controllers/v1/model.py`
- [ ] 4.2 实现 `GET /api/v1/models` 接口返回提供商和模型列表
- [ ] 4.3 创建模型列表响应 Schema
- [ ] 4.4 创建前端组件 `web/vue/src/ai/components/ModelSelector.vue`
- [ ] 4.5 实现提供商分组选择器 UI
- [ ] 4.6 实现模型选择同步到 useChat body.model
- [ ] 4.7 替换 ChatPage 中的静态模型选择器

## 5. 测试与验证

- [ ] 5.1 后端单元测试：Callback Handler 事件格式
- [ ] 5.2 后端集成测试：会话列表接口
- [ ] 5.3 后端集成测试：模型列表接口
- [ ] 5.4 前端组件测试：ModelSelector
- [ ] 5.5 前端组件测试：ConversationListPage
- [ ] 5.6 E2E 测试：完整对话流程含工具调用
