# 会话持久化与任务管控技术设计

## 上下文

### 背景

LLM 对话接口需要持久化会话和消息数据，支持：
- 会话恢复：用户可继续之前的对话
- 历史查询：查看对话历史记录
- 统计分析：token 使用统计、对话轮数统计
- 任务管控：停止正在进行的对话、超时自动清理

### 当前状态

```
已有组件：
├── framework/database/           # ORM 基类、迁移工具
├── framework/pubsub/             # Redis PubSub 发布订阅
├── framework/configs/            # 配置管理
└── framework/common/ctx.py       # 租户上下文

缺失组件：
├── ai/models/conversation.py     # 会话模型 ← 本次迁移
├── ai/models/message.py          # 消息模型 ← 本次迁移
└── ai/listeners/services/pubsub/memory_task/      # 任务管控 ← 本次迁移
```

### 约束

1. 必须使用 `create_module_base("ai")` 创建模块级 Base
2. 必须复用 `framework/pubsub/` 实现跨进程任务停止
3. 数据库表必须归属 `ai` schema
4. 遵循三层架构，Model 层只负责数据存储

## 目标 / 非目标

**目标：**

1. 实现 `Conversation` 和 `Message` ORM 模型
2. 实现后台任务管控服务（停止、超时清理）
3. 复用 `framework/pubsub/` 实现跨进程通信
4. 支持租户隔离和多应用场景

**非目标：**

1. 会话摘要生成（由 LangChain Memory 处理）
2. 会话分享和权限管理（超出本次范围）
3. 消息搜索和向量索引（超出本次范围）

## 决策

### 决策 1：ORM 模型设计

**选择**：独立 `ai` schema，两张表（conversations + messages）

**理由**：
- 与现有模块隔离（demo、iam、tenant 各有独立 schema）
- 会话和消息是 1:N 关系，分开存储便于查询和维护
- 消息表数据量大，独立存储便于后续分表或归档

**表结构**：

```
ai.conversations
├── id (UUID, PK)
├── tenant_id (String, indexed)
├── app_id (String, indexed)
├── name (String)
├── status (Enum: normal/archived/deleted)
├── mode (Enum: chat/completion/workflow)
├── created_at, updated_at
└── indexes: (tenant_id, app_id, status)

ai.messages
├── id (UUID, PK)
├── conversation_id (UUID, FK → conversations.id)
├── role (Enum: user/assistant/system/tool)
├── content (Text)
├── status (Enum: pending/completed/error/stopped)
├── query (Text) — 用户问题
├── answer (Text) — 助手回复（非流式时存储）
├── message_metadata (JSONB) — 扩展字段
├── token_count (Integer) — token 统计
├── created_at, updated_at
└── indexes: (conversation_id, created_at)
```

### 决策 2：任务管控架构

**选择**：Redis PubSub + asyncio 任务管理

**理由**：
- 项目已有 `framework/pubsub/` 组件，可直接复用
- PubSub 支持跨进程通信，适合多 Worker 场景
- asyncio 任务管理用于单进程内的任务取消

**架构**：

```
停止任务流程：
┌─────────────┐    POST /stop    ┌─────────────┐
│   Client    │ ───────────────▶ │  Worker A   │
└─────────────┘                  └──────┬──────┘
                                        │
                                        │ PubSub publish
                                        ▼
                                 ┌─────────────┐
                                 │   Redis     │
                                 └──────┬──────┘
                                        │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                  ┌───────────┐  ┌───────────┐  ┌───────────┐
                  │ Worker A  │  │ Worker B  │  │ Worker C  │
                  │ (订阅)    │  │ (订阅)    │  │ (订阅)    │
                  └───────────┘  └───────────┘  └───────────┘
                         │
                         │ 匹配 task_id
                         ▼
                  取消 asyncio 任务
```

### 决策 3：超时清理策略

**选择**：定时检查 + 配置化超时时间

**理由**：
- 超时时间通过配置文件设置，支持不同环境不同配置
- 定时检查任务使用 APScheduler（项目已集成）
- 清理时发送结束信号并更新消息状态为 `stopped`

**配置**：

```yaml
# config/application.yml
workflow:
  task_cleanup_timeout: 600  # 10 分钟
```

### 决策 4：消息状态机

**选择**：明确的状态枚举和状态流转

**状态流转**：

```
pending → completed (正常完成)
pending → error (发生错误)
pending → stopped (被停止)
```

**理由**：
- 状态清晰，便于监控和统计
- 防止非法状态转换

## 风险 / 权衡

### 风险 1：消息表数据量增长

**风险**：高频对话场景下消息表数据量快速增长

**缓解措施**：
- 为 `conversation_id` 和 `created_at` 创建复合索引
- 后续可考虑分区表或定期归档
- 消息内容压缩存储（可选）

### 风险 2：PubSub 消息丢失

**风险**：Redis PubSub 不持久化，消息可能丢失

**缓解措施**：
- Worker 重启时重新订阅
- 任务超时清理作为兜底机制
- 记录任务状态到 Redis（可选增强）

### 风险 3：跨 Schema 外键

**风险**：消息表可能需要引用其他 schema 的表

**缓解措施**：
- 本次迁移不涉及跨 Schema 外键
- 如需引用用户表，使用应用层一致性检查
- 遵循项目规范：跨模块数据引用不使用外键约束

## 迁移计划

### 阶段 1：ORM 模型（约 2 小时）

1. 创建 `ai/models/__init__.py`，使用 `create_module_base("ai")`
2. 创建 `ai/models/enums.py`，定义状态枚举
3. 创建 `ai/models/conversation.py`
4. 创建 `ai/models/message.py`
5. 创建 Alembic 迁移脚本

### 阶段 2：任务管控服务（约 2-3 小时）

1. 创建 `ai/listeners/services/pubsub/memory_task/` 目录
2. 迁移 `constants.py` 任务类型常量
3. 迁移 `cancel_asyncio_task.py` PubSub 订阅处理器
4. 迁移 `helpers.py` stop_task_by_id
5. 迁移 `cleanup.py` cleanup_task_after_timeout
6. 适配 `framework/pubsub/` 组件

### 阶段 3：集成测试（约 1-2 小时）

1. 编写 ORM 模型 CRUD 测试
2. 编写任务停止测试
3. 编写超时清理测试
4. 编写多租户隔离测试

### 回滚策略

- 删除 `ai/models/` 和 `ai/listeners/services/pubsub/memory_task/` 目录
- 执行 Alembic downgrade 回滚数据库迁移
