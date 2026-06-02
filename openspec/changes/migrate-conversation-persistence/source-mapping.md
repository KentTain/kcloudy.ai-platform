# Alon 项目源文件映射

本文档记录 `migrate-conversation-persistence` 变更对应的 Alon 项目源文件路径，供实现时参考。

## 源项目路径

```
ALON_ROOT=D:\Project\ai\Alon\packages\platform
```

## 文件映射表

### 1. Conversation 模型迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/models/conversation.py` | `{ALON_ROOT}/src/alon/models/conversation.py` |

### 2. Message 模型迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/models/message.py` | `{ALON_ROOT}/src/alon/models/message.py` |

### 3. 枚举定义迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/models/enums.py` | `{ALON_ROOT}/src/alon/models/enums.py` |

### 4. ORM 基类参考

| 目标路径 | Alon 源路径 |
|----------|-------------|
| 参考 `src/ai/models/core/base.py` | `{ALON_ROOT}/src/alon/models/core/base.py` |
| 参考 `src/ai/models/core/engine.py` | `{ALON_ROOT}/src/alon/models/core/engine.py` |
| 参考 `src/ai/models/mixins/active_record.py` | `{ALON_ROOT}/src/alon/models/mixins/active_record.py` |

> **注意**：本项目使用 `framework/database/` 提供的基类和 Mixin，只需参考 Alon 的字段定义。

### 5. 任务管控服务迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/services/memory_task/__init__.py` | `{ALON_ROOT}/src/alon/listeners/services/pubsub/memory_task/__init__.py` |
| `src/ai/services/memory_task/constants.py` | `{ALON_ROOT}/src/alon/listeners/services/pubsub/memory_task/constants.py` |
| `src/ai/services/memory_task/helpers.py` | `{ALON_ROOT}/src/alon/listeners/services/pubsub/memory_task/helpers.py` |
| `src/ai/services/memory_task/cleanup.py` | `{ALON_ROOT}/src/alon/listeners/services/pubsub/memory_task/cleanup.py` |
| `src/ai/services/memory_task/cancel_asyncio_task.py` | `{ALON_ROOT}/src/alon/listeners/services/pubsub/memory_task/cancel_asyncio_task.py` |

## 导入路径替换规则

迁移时需要批量替换导入路径：

| Alon 导入路径 | 目标导入路径 |
|---------------|--------------|
| `from alon.models.conversation` | `from ai.models.conversation` |
| `from alon.models.message` | `from ai.models.message` |
| `from alon.models.enums` | `from ai.models.enums` |
| `from alon.models.core.base` | `from framework.database.core.base` |
| `from alon.models.core.engine` | `from framework.database.core.engine` |
| `from alon.models.mixins.active_record` | `from framework.database.mixins.active_record` |
| `from alon.configs.settings` | `from framework.configs.settings` |
| `from alon.common.ctx` | `from framework.common.ctx` |
| `from alon.extensions.ext_redis` | `from framework.cache.redis_util` 或 `from framework.pubsub` |

## 关键依赖适配

### ORM 基类

```python
# Alon 使用
from alon.models.core.base import Base
from alon.models.mixins.active_record import ActiveRecordMixin

# 改为使用 framework
from framework.database import create_module_base, create_base_model

Base = create_module_base("ai")
BaseModel = create_base_model(Base)
```

### 数据库会话

```python
# Alon 使用
from alon.models.core.engine import async_session

# 改为使用 framework
from framework.database.core.engine import get_async_session
```

### PubSub

```python
# Alon 使用
from alon.extensions.ext_redis import redis_client

# 改为使用 framework
from framework.pubsub import get_pubsub_provider
```

### 配置读取

```python
# Alon 使用
from alon.configs.settings import settings

# 改为使用 framework
from framework.configs.settings import settings
# 超时配置：settings.workflow.task_cleanup_timeout
```

## 表结构参考

### conversations 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| tenant_id | String(36) | 租户 ID |
| app_id | String(36) | 应用 ID |
| name | String(255) | 会话名称 |
| status | String(20) | 状态枚举 |
| mode | String(20) | 模式枚举 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### messages 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| conversation_id | UUID | 外键 → conversations.id |
| role | String(20) | 角色枚举 |
| content | Text | 消息内容 |
| status | String(20) | 状态枚举 |
| query | Text | 用户问题 |
| answer | Text | 助手回复 |
| message_metadata | JSONB | 扩展元数据 |
| token_count | Integer | token 数量 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 迁移优先级

### 第一优先级（核心功能，必须迁移）

1. `models/enums.py` - 状态枚举定义
2. `models/conversation.py` - 会话模型
3. `models/message.py` - 消息模型
4. `services/memory_task/constants.py` - 任务类型常量
5. `services/memory_task/cancel_asyncio_task.py` - asyncio 取消逻辑
6. `services/memory_task/helpers.py` - 任务停止函数
7. `services/memory_task/cleanup.py` - 超时清理函数

### 第二优先级（数据库迁移）

1. `migrations/env.py` - 迁移环境配置
2. `migrations/versions/xxx_create_conversation_tables.py` - 建表脚本

## 文件数量统计

| 类别 | 文件数 |
|------|--------|
| 必须迁移 | 7 |
| 数据库迁移 | 2 |
| 测试文件 | 6 |
| 文档 | 2 |
| **总计** | **17** |

## 注意事项

1. **Schema 隔离**：所有表必须归属于 `ai` schema，使用 `create_module_base("ai")`
2. **外键处理**：跨 Schema 外键需要特殊处理，本项目 conversation 和 message 同属 ai schema，可直接使用外键
3. **迁移配置**：`migrations/env.py` 必须设置 `version_table_schema="ai"`
