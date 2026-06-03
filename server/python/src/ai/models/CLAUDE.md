# AI Models 模块

会话持久化与消息模型，归属于 `ai` PostgreSQL schema。

## 模型

| 模型 | 表名 | 说明 |
|------|------|------|
| Conversation | conversations | 会话，支持租户隔离和多应用 |
| Message | messages | 消息，外键关联 Conversation |

## 枚举

| 枚举 | 值 | 说明 |
|------|------|------|
| ConversationStatus | normal / archived / deleted | 会话状态，deleted 为软删除 |
| ConversationMode | chat / completion / workflow | 会话模式 |
| MessageStatus | pending / completed / error / stopped | 消息状态 |
| MessageRole | user / assistant / system / tool | 消息角色 |

## Mixin 组合

所有模型继承 `BaseModel`（含 id/created_at/updated_at）+ `ActiveRecordMixin`（CRUD 方法）+ `TenantMixin`（tenant_id 租户隔离）。

## 消息状态流转

```
pending → completed (正常完成)
pending → error (发生错误)
pending → stopped (被用户停止)
```

## 外键

- `messages.conversation_id` → `ai.conversations.id`（同 schema，CASCADE 删除）
