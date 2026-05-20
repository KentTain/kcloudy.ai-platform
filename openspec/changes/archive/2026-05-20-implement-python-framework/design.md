## Context

当前项目需要从参考项目 `Alon` 迁移成熟的基础设施代码到 `framework` 模块。目标技术栈为 Python，使用 FastAPI + SQLAlchemy 2.0。项目基础设施包括 PostgreSQL、Redis、MinIO。

参考项目结构：
- `D:\Project\ai\Alon\packages\platform\src\alon\` - Python 参考实现
- `D:\Project\kcloudy\java\Common\` - Java 参考实现（租户模型）

## Goals / Non-Goals

**Goals:**
- 创建可复用的 `framework` 模块，包含 11 个子模块
- 使用 Python Protocol 定义核心接口，支持多种实现
- 实现配置驱动的组件加载机制
- 创建统一的 `RedisUtil` 工具类
- 为所有功能编写单元测试
- 重构 `demo` 模块使其依赖 `framework`

**Non-Goals:**
- 不实现其他技术栈（Java、NetCore、Rust）
- 不实现租户功能的具体逻辑（仅模型设计）
- 不做集成测试
- 不实现 RabbitMQ 等其他消息中间件（仅 Redis）

## Decisions

### 1. 目录结构设计

```
server/python/src/
├── framework/                 # 通用模块
│   ├── config/               # 配置加载
│   ├── cache/                # Redis 缓存
│   ├── core/                 # 接口定义
│   ├── common/               # 通用组件
│   ├── storage/              # 存储实现
│   ├── queue/                # 队列实现
│   ├── lock/                 # 锁实现
│   ├── pubsub/               # 发布订阅
│   ├── database/             # 数据库通用
│   ├── tenant/               # 租户模型
│   └── utils/                # 工具函数
└── tests/framework/          # 单元测试
```

**理由**: 遵循需求文档定义的结构，保持模块边界清晰。

### 2. 核心接口设计（Python Protocol）

```python
# core/storage.py
class StorageProvider(Protocol):
    async def upload(self, bucket: str, name: str, data: bytes) -> str: ...
    async def download(self, bucket: str, name: str) -> bytes: ...
    async def delete(self, bucket: str, name: str) -> bool: ...
    async def get_presigned_url(self, bucket: str, name: str, expires: int) -> str: ...

# core/queue.py
class QueueProvider(Protocol):
    async def enqueue(self, queue: str, message: dict) -> str: ...
    async def dequeue(self, queue: str, count: int) -> list[Message]: ...
    async def ack(self, queue: str, message_id: str) -> bool: ...

# core/pubsub.py
class PubSubProvider(Protocol):
    async def publish(self, topic: str, message: dict) -> bool: ...
    async def subscribe(self, topic: str, handler: Callable) -> None: ...

# core/lock.py
class LockProvider(Protocol):
    async def acquire(self, key: str, ttl: int, timeout: int | None) -> Lock: ...
    async def release(self, lock: Lock) -> bool: ...
    async def extend(self, lock: Lock, ttl: int) -> bool: ...
```

**理由**: Python Protocol 提供结构化子类型（静态鸭子类型），支持类型检查且无需继承。

### 3. 配置驱动的工厂模式

```python
# storage/factory.py
def get_storage_provider(config: OssSettings) -> StorageProvider:
    match config.default_type:
        case "minio": return MinioStorage(config.minio)
        case "aliyun": return AliyunStorage(config.aliyun)
        case "tencent": return TencentStorage(config.tencent)

# queue/factory.py
def get_queue_provider(config: MessagingSettings) -> QueueProvider:
    match config.queue.use:
        case "redis": return RedisQueue(config.connections.redis)

# pubsub/factory.py
def get_pubsub_provider(config: MessagingSettings) -> PubSubProvider:
    match config.pubsub.use:
        case "redis": return RedisPubSub(config.connections.redis)

# lock/factory.py
def get_lock_provider(config: LockSettings, redis: RedisUtil) -> LockProvider:
    match config.provider:
        case "redis": return RedisLock(redis)
        case "sqlalchemy": return DatabaseLock()
```

**理由**: 遵循参考项目的工厂模式，通过配置切换实现。

### 4. RedisUtil 统一工具类

```python
# cache/redis_util.py
class RedisUtil:
    """统一的 Redis 工具类，所有 Redis 操作通过此类"""

    _client: Redis | None = None
    _pool: ConnectionPool | None = None

    @classmethod
    async def init(cls, config: RedisSettings) -> None: ...

    @classmethod
    async def get(cls, key: str) -> str | None: ...

    @classmethod
    async def set(cls, key: str, value: str, ttl: int | None = None) -> bool: ...

    @classmethod
    async def acquire_lock(cls, key: str, value: str, ttl: int) -> bool: ...

    @classmethod
    async def release_lock(cls, key: str, value: str) -> bool: ...

    # Stream 操作 (Queue)
    @classmethod
    async def xadd(cls, stream: str, fields: dict) -> str: ...

    @classmethod
    async def xread(cls, streams: dict, count: int) -> list: ...

    # Pub/Sub
    @classmethod
    async def publish(cls, channel: str, message: str) -> int: ...
```

**理由**: 统一 Redis 操作入口，避免多处管理连接，便于测试和维护。

### 5. 数据库模块结构

```
database/
├── core/
│   ├── base.py          # Base 模型类
│   ├── engine.py        # 引擎管理
│   └── schema.py        # Schema 工具
├── events/
│   ├── audit.py         # 审计事件
│   └── tenant.py        # 租户事件
├── interceptors/
│   └── query.py         # 查询拦截器
├── mixins/
│   ├── audit.py         # 审计混入
│   ├── tenant.py        # 租户混入
│   └── tree.py          # 树结构混入
├── types/
│   ├── uuid.py          # UUID 类型
│   ├── snowflake.py     # 雪花ID类型
│   ├── datetime.py      # 时间类型
│   └── enum.py          # 枚举类型
└── __init__.py
```

**理由**: 直接迁移参考项目的成熟实现，保持一致性。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| 迁移代码与现有 demo 不兼容 | 增量迁移，保持接口兼容，完成后统一重构 |
| Redis 连接池管理复杂 | 复用参考项目的连接管理器，支持单机/集群/哨兵 |
| 单元测试覆盖不足 | 每个模块迁移后立即编写测试 |
| 配置加载顺序问题 | 使用 Pydantic 进行配置验证，明确依赖关系 |

## Migration Plan

**阶段 1: 基础层**
1. 创建 `config/` 模块，迁移配置加载逻辑
2. 创建 `common/` 模块，迁移异常和上下文
3. 创建 `utils/` 模块，迁移工具函数

**阶段 2: Redis 基础设施**
4. 创建 `cache/` 模块，实现 RedisUtil

**阶段 3: 核心抽象 + 实现**
5. 创建 `core/` 模块，定义 Protocol 接口
6. 创建 `lock/` 模块，基于 RedisUtil 实现
7. 创建 `storage/` 模块，实现 MinIO 存储
8. 创建 `queue/` 模块，实现 Redis Queue
9. 创建 `pubsub/` 模块，实现 Redis PubSub

**阶段 4: 数据层**
10. 创建 `database/` 模块，完整迁移
11. 创建 `tenant/` 模块，仅模型设计

**阶段 5: 验证**
12. 重构 `demo` 模块
13. 编写单元测试
