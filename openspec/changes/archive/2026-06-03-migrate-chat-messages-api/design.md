# LLM 对话接口技术设计

## 上下文

### 背景

完成所有前置变更后，需要实现 `/chat-messages` 接口本体，整合：
- `LLMService`：统一模型调用
- `AlonChatModel`：LangChain 桥接
- `AgentFactory`：LangGraph Agent 创建
- `Conversation/Message`：会话持久化
- `memory_task`：任务管控

### 当前状态

```
已完成（或待完成）的前置变更：
├── migrate-model-component → LLMService
├── migrate-langchain-bridge → AlonChatModel, AgentFactory
└── migrate-conversation-persistence → Conversation, Message, memory_task

本次变更：
└── ai/controllers/v1/chat/llm.py  ← 接口实现
```

### 约束

1. 必须使用 LangGraph 构建 Agent 流程
2. 必须返回 SSE 格式的流式响应
3. 必须支持会话创建和恢复
4. 必须支持任务停止
5. SSE 格式与 Alon 平台兼容

## 目标 / 非目标

**目标：**

1. 实现 `POST /api/v1/chat-messages` 流式对话接口
2. 实现 `POST /api/v1/chat-messages/:id/stop` 任务停止接口
3. 支持会话创建（新会话）和恢复（已有会话）
4. 返回 SSE 格式的流式响应
5. 集成任务停止和超时清理机制

**非目标：**

1. 会话管理接口（列表、删除、归档）
2. 多模态消息（图片、文件）- 后续扩展
3. 工具调用结果展示 - 后续扩展

## 决策

### 决策 1：使用 LangGraph 构建 Agent

**选择**：使用 LangGraph 而非 AgentExecutor

**理由**：
- LangGraph 支持状态管理和中断恢复
- 项目已有 LangGraph 使用经验
- 更灵活的工作流控制

**架构**：

```
请求流程：
┌─────────────┐
│  Controller │
│  chat_messages()
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  1. 创建/恢复会话                               │
│  2. 创建 AlonChatModel                         │
│  3. 创建 LangGraph Agent                       │
│  4. 创建 PostgresChatMessageHistory (可选)     │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Agent.astream_events()                        │
│  ├─ on_chat_model_stream → SSE message 事件    │
│  ├─ on_tool_start → SSE search_keywords 事件   │
│  ├─ on_tool_end → (内部处理)                   │
│  └─ on_chain_end → SSE finish 事件             │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  保存消息到数据库                              │
│  更新 token 统计                               │
└─────────────────────────────────────────────────┘
```

### 决策 2：SSE 响应格式

**选择**：与 Alon 平台兼容的 SSE 格式

**格式定义**：

```
事件类型：message（内容块）
data: {"event": "message", "data": {"content": "你好"}}

事件类型：finish（完成）
data: {"event": "finish", "data": {"prompt_tokens": 10, "completion_tokens": 20}}

事件类型：search_keywords（搜索）
data: {"event": "search_keywords", "data": {"keywords": ["关键词1"]}}

事件类型：error（错误）
data: {"event": "error", "data": {"code": "MODEL_ERROR", "message": "..."}}
```

**实现方式**：
- 使用 `StreamingResponse` + 自定义生成器
- 每个事件以 `\n\n` 结尾
- 错误时发送 error 事件并结束流

### 决策 3：会话管理策略

**选择**：基于 `conversation_id` 的会话管理

**流程**：

```
会话创建：
├─ 请求不包含 conversation_id
├─ 创建新 Conversation 记录
├─ 创建第一条 Message（status=pending）
└─ 返回新生成的 conversation_id

会话恢复：
├─ 请求包含 conversation_id
├─ 验证会话存在且属于当前租户
├─ 加载历史消息（可选，由 LangGraph checkpointer 处理）
└─ 创建新 Message（status=pending）
```

### 决策 4：任务停止实现

**选择**：通过 PubSub 发送停止信号

**流程**：

```
停止请求：
┌─────────────┐
│  Controller │
│  stop_chat_messages()
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  1. 验证会话存在且属于当前租户                  │
│  2. 获取当前活跃的 task_id                     │
│  3. 调用 stop_task_by_id()                     │
│  4. 更新消息状态为 stopped                     │
└─────────────────────────────────────────────────┘
```

### 决策 5：APP_ID 配置

**选择**：配置化的 APP_ID

**理由**：
- Alon 原代码硬编码固定 ID
- 本项目支持多应用场景，需配置化

**配置**：

```yaml
# config/application.yml
app:
  default_app_id: "00000000-0000-0000-0000-000000000001"
  default_app_name: "通用智能体"
```

## 风险 / 权衡

### 风险 1：流式响应中断

**风险**：客户端断开连接导致资源泄漏

**缓解措施**：
- 使用 `try/finally` 确保资源清理
- 记录完整的 token 统计
- 更新消息状态为 `error` 或 `stopped`

### 风险 2：并发会话冲突

**风险**：同一会话并发请求导致状态混乱

**缓解措施**：
- 检查会话是否有活跃任务
- 拒绝已有活跃任务的会话的新请求
- 或自动停止前一个任务

### 风险 3：LangGraph 版本兼容性

**风险**：LangGraph API 变化

**缓解措施**：
- 锁定 `langgraph==1.2.0`
- 参考项目已有的 LangGraph 示例
- 升级前充分测试

## 迁移计划

### 阶段 1：Schema 定义（约 1 小时）

1. 创建 `ai/schemas/completion.py`
2. 定义 `ModelConfig` Schema
3. 定义 `SearchConfig` Schema
4. 定义 `LLMChatCompletion` 请求 Schema
5. 定义 SSE 事件 Schema

### 阶段 2：控制器实现（约 3-4 小时）

1. 创建 `ai/controllers/v1/chat/llm.py`
2. 实现 `chat_messages()` 流式对话方法
3. 实现会话创建/恢复逻辑
4. 实现 SSE 生成器
5. 实现 `stop_chat_messages()` 停止方法
6. 集成任务管控

### 阶段 3：路由注册（约 0.5 小时）

1. 在 `ai/module.py` 中注册路由
2. 配置路由前缀和标签

### 阶段 4：测试验证（约 2 小时）

1. 编写接口测试
2. 测试流式响应
3. 测试会话创建/恢复
4. 测试任务停止
5. 测试错误处理

### 回滚策略

- 删除 `ai/controllers/v1/chat/` 和 `ai/schemas/completion.py`
- 移除路由注册
- 不涉及数据库变更
