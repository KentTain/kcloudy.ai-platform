# 会话持久化与任务管控迁移任务清单

## 1. 基础设施搭建

- [x] 1.1 创建 `ai/models/__init__.py`，使用 `create_module_base("ai")`
- [x] 1.2 创建 `ai/services/__init__.py`
- [x] 1.3 创建 `ai/listeners/__init__.py`
- [x] 1.4 创建 `ai/listeners/services/__init__.py`
- [x] 1.5 创建 `ai/listeners/services/pubsub/__init__.py`
- [x] 1.6 创建 `ai/listeners/services/pubsub/constants.py`（任务停止通道常量）
- [x] 1.7 创建 `ai/listeners/services/pubsub/memory_task/__init__.py`

## 2. 枚举定义

- [x] 2.1 创建 `ai/models/enums.py`
- [x] 2.2 定义 `ConversationStatus` 枚举（normal/archived/deleted）
- [x] 2.3 定义 `ConversationMode` 枚举（chat/completion/workflow）
- [x] 2.4 定义 `MessageStatus` 枚举（pending/completed/error/stopped）
- [x] 2.5 定义 `MessageRole` 枚举（user/assistant/system/tool）

## 3. Conversation 模型实现

- [x] 3.1 创建 `ai/models/conversation.py`
- [x] 3.2 定义 `Conversation` 类继承 `BaseModel`
- [x] 3.3 定义字段：id、tenant_id、app_id、name、status、mode
- [x] 3.4 添加时间戳 Mixin（created_at、updated_at）
- [x] 3.5 定义索引：tenant_id、app_id、status
- [x] 3.6 实现 `ActiveRecordMixin` 方法

## 4. Message 模型实现

- [x] 4.1 创建 `ai/models/message.py`
- [x] 4.2 定义 `Message` 类继承 `BaseModel`
- [x] 4.3 定义字段：id、conversation_id、role、content、status、query、answer、token_count、message_metadata
- [x] 4.4 添加时间戳 Mixin
- [x] 4.5 定义外键关联到 Conversation
- [x] 4.6 定义索引：conversation_id、created_at
- [x] 4.7 实现 `ActiveRecordMixin` 方法

## 5. 数据库迁移

- [x] 5.1 创建 `ai/migrations/` 目录结构
- [x] 5.2 配置 `ai/migrations/env.py`，设置 `version_table_schema="ai"`
- [x] 5.3 创建 Alembic 迁移脚本 `005_create_conversation_tables.py`
- [x] 5.4 定义 `ai.conversations` 表
- [x] 5.5 定义 `ai.messages` 表
- [x] 5.6 创建索引和约束
- [x] 5.7 执行迁移验证表结构

## 6. 任务管控服务实现

- [x] 6.1 创建 `ai/listeners/services/pubsub/memory_task/constants.py`，定义任务类型常量
- [x] 6.2 创建 `ai/listeners/services/pubsub/memory_task/cancel_asyncio_task.py`
- [x] 6.3 实现 CancelAsyncioTaskHandler(SingleTopicHandler)，订阅任务停止通道
- [x] 6.4 创建 `ai/listeners/services/pubsub/memory_task/helpers.py`
- [x] 6.5 实现 `stop_task_by_id()` 函数，使用 PubSub 发布停止信号
- [x] 6.6 创建 `ai/listeners/services/pubsub/memory_task/cleanup.py`
- [x] 6.7 实现 `cleanup_task_after_timeout()` 函数
- [x] 6.8 实现活跃任务跟踪（ACTIVE_CLEANUP_TASKS）

## 7. PubSub 集成

- [x] 7.1 在 Worker 启动时订阅任务停止通道
- [x] 7.2 实现停止信号处理器
- [x] 7.3 匹配 task_id 并取消对应 asyncio 任务
- [x] 7.4 更新消息状态为 stopped

## 8. 配置集成

- [x] 8.1 在 `framework/configs/settings.py` 添加 workflow 配置
- [x] 8.2 添加 `task_cleanup_timeout` 配置项
- [x] 8.3 验证配置读取正确

## 9. 测试

- [x] 9.1 编写 Conversation 模型 CRUD 测试
- [x] 9.2 编写 Message 模型 CRUD 测试
- [x] 9.3 编写多租户隔离测试
- [x] 9.4 编写任务停止测试
- [x] 9.5 编写超时清理测试
- [x] 9.6 编写 PubSub 信号传递测试

## 10. 文档与收尾

- [x] 10.1 创建 `ai/models/CLAUDE.md` 模块文档
- [x] 10.2 创建 `ai/listeners/services/pubsub/memory_task/CLAUDE.md` 模块文档
- [x] 10.3 运行完整测试套件验证
- [ ] 10.4 代码审查和清理
