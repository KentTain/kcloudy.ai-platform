## 上下文

### 当前状态

**阶段一已完成**（ai-chat-module）：
- 前端：基础对话页面（ChatPage.vue），使用 useChat hook
- 后端：un_llm_task() 直接处理 SSE 事件，输出 AI SDK 格式
- SSE 格式：完全采用 AI SDK UIMessageChunk 标准
- 模型选择：前端静态配置（固定列表）

**技术债**：
- un_llm_task() 直接处理 SSE 格式化，职责不清
- 工具调用事件已支持但前端无可视化
- 缺少会话管理页面
- 模型列表为静态配置

### 约束

- 复用现有 Conversation、Message 模型
- 后端 SSE 格式保持不变（前端无感知）
- ai-elements-vue 组件已在 components/ai-elements/

## 目标 / 非目标

**目标：**

1. 引入 UIMessageChunkCallbackHandler 分离 SSE 格式化职责
2. 工具调用可视化（tool、confirmation 组件）
3. 会话管理页面（列表、切换、删除）
4. 模型选择器组件（动态获取提供商/模型列表）

**非目标：**

1. 不新增数据库表结构
2. 不改造 LangChain Agent 核心逻辑
3. 不支持多模态图片上传
4. 不实现联网搜索可视化

## 决策

### 1. UIMessageChunkCallbackHandler 设计

**选择**：继承 LangChain AsyncCallbackHandler，拦截事件流

**架构**：
`
agent.astream_events() → UIMessageChunkCallbackHandler → event_queue
                                      ↓
                            SSE 格式化逻辑
`

**职责边界**：
- un_llm_task()：启动 Agent、管理任务生命周期、异常处理
- CallbackHandler：接收事件、转换为 AI SDK 格式、发送到队列

**替代方案**：
- 继续在 un_llm_task() 中处理：职责耦合，不利于扩展
- 新增中间层：增加复杂度，Callback Handler 已足够

**实现要点**：
- 使用 syncio.Queue 传递事件
- 支持 on_chat_model_stream、on_tool_start、on_tool_end 事件
- 输出 AI SDK 标准格式（与阶段一一致）

### 2. 工具调用可视化

**选择**：使用 ai-elements-vue 的 	ool、confirmation 组件

**组件位置**：web/vue/src/components/ai-elements/

**SSE 事件格式**：
`
data: {"type":"tool-call","toolCallId":"call-xxx","toolName":"search","args":{...}}
data: {"type":"tool-result","toolCallId":"call-xxx","result":"..."}
`

**前端集成**：
- ChatPage.vue 检测消息中的 	oolInvocations 字段
- 渲染 ToolCall 组件展示工具名称、参数、状态
- 工具确认功能暂不实现（阶段三）

**替代方案**：
- 自研组件：开发成本高，ai-elements-vue 已提供

### 3. 会话管理页面

**选择**：新增独立页面 ConversationListPage.vue

**路由**：/ai/conversations

**功能**：
- 列表展示：会话名称、创建时间、消息数量
- 切换会话：点击跳转到 ChatPage 并加载历史消息
- 删除会话：调用 DELETE /api/v1/conversations/{id}

**后端接口**：
`
GET /api/v1/conversations
  Response: [{ id, name, created_at, message_count }]

DELETE /api/v1/conversations/{id}
  Response: { success: true }
`

**数据模型**：复用现有 Conversation 模型

### 4. 模型选择器组件

**选择**：新增 ModelSelector.vue 组件

**后端接口**：
`
GET /api/v1/models
  Response: {
    providers: [{ id, name, models: [{ id, name, description }] }]
  }
`

**前端实现**：
- 使用 shadcn-vue 的 Select 组件
- 分组展示：按提供商分组
- 动态加载：组件挂载时请求模型列表
- 回显当前选择：通过 useChat 的 ody.model 获取

**后端实现**：
- 遍历 ProviderConfiguration 获取已配置的提供商
- 每个提供商返回可用模型列表
- 支持按租户过滤（可选）

**替代方案**：
- 继续使用静态配置：无法动态感知后端模型变化
- 硬编码模型列表：维护成本高

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| Callback Handler 与直接修改行为不一致 | 单元测试覆盖所有事件类型 |
| ai-elements-vue tool 组件 API 变化 | 锁定版本，必要时复制源码修改 |
| 会话列表大数据量性能问题 | 分页加载（阶段三） |
| 模型列表接口暴露敏感配置 | 仅返回已配置且启用的模型 |

## 迁移计划

### 阶段二实施顺序

1. **后端重构**：引入 UIMessageChunkCallbackHandler
   - 新增 server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py
   - 修改 un_llm_task() 使用 Callback Handler
   - 验证 SSE 格式与阶段一一致

2. **工具调用可视化**：
   - 安装 ai-elements-vue tool 组件
   - 修改 ChatPage.vue 集成组件
   - 后端已支持工具事件（无需修改）

3. **会话管理**：
   - 新增后端接口 conversation.py
   - 新增前端页面 ConversationListPage.vue
   - 配置路由和菜单

4. **模型选择器**：
   - 新增后端接口 model.py
   - 新增前端组件 ModelSelector.vue
   - 替换 ChatPage 中的静态选择器

### 回滚策略

- 每个 task 独立提交，可单独回滚
- Callback Handler 失败可回退到直接修改方式
