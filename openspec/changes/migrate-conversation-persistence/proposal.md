# 会话持久化与任务管控迁移提案

## 为什么

LLM 对话接口需要持久化会话和消息数据，以支持会话恢复、历史查询、统计分析等功能。同时需要后台任务管控机制，支持任务停止、超时清理等能力。

此变更与 `migrate-model-component` 和 `migrate-langchain-bridge` 可并行开发，互不依赖。

## 变更内容

从 Alon 平台迁移会话持久化与任务管控模块：

- 新增 `Conversation` 和 `Message` ORM 模型：支持会话/消息的 CRUD 操作
- 新增会话状态枚举：`normal`、`archived`、`deleted`
- 新增消息状态枚举：`pending`、`completed`、`error`、`stopped`
- 新增后台任务管控服务：支持任务停止、超时清理
- 复用 `framework/pubsub/` 实现跨进程任务停止信号

**不包含**：会话摘要生成（由 LangChain Memory 处理）。

## 功能 (Capabilities)

### 新增功能

- `conversation-model`: 会话 ORM 模型，支持会话创建、恢复、归档、删除，包含租户隔离和多应用支持
- `message-model`: 消息 ORM 模型，支持消息持久化、状态跟踪、token 统计
- `memory-task`: 后台任务管控服务，支持任务停止（通过 PubSub）、超时自动清理、asyncio 任务取消

### 修改功能

无（全新功能模块）。

## 影响

### 代码结构

```
ai/models/
├── __init__.py                   # create_module_base("ai")
├── conversation.py               # Conversation 模型
├── message.py                    # Message 模型
└── enums.py                      # ConversationStatus, MessageStatus

ai/listeners/services/pubsub/memory_task/
├── __init__.py
├── constants.py                  # ACTIVE_ASYNCIO_TASKS / TASK_TYPE_GENERATE_LLM
├── cancel_asyncio_task.py        # CancelAsyncioTaskHandler (PubSub 订阅)
├── helpers.py                    # stop_task_by_id
└── cleanup.py                    # cleanup_task_after_timeout

ai/migrations/
└── versions/
    └── xxx_create_conversation_tables.py
```

### 数据库变更

| 表名 | Schema | 说明 |
|------|--------|------|
| `conversations` | `ai` | 会话表 |
| `messages` | `ai` | 消息表 |

### 依赖组件

| 组件 | 用途 | 状态 |
|------|------|------|
| `framework/database/` | ORM 基类和迁移工具 | ✅ 可用 |
| `framework/pubsub/` | 跨进程任务停止信号 | ✅ 可用 |
| `framework/configs/` | 超时配置读取 | ✅ 可用 |

### API 端点

此变更不直接暴露 API 端点，为后续 `/chat-messages` 接口提供数据持久化能力。

### 兼容性

- 无破坏性变更
- 新增模块，不影响现有功能
- 新增数据库表，需要执行迁移
