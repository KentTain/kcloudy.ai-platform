# Framework 模块详细设计文档

## 概述

Framework 是 Python 后端的核心基础设施模块，为上层业务模块提供统一的技术能力支撑。采用依赖倒置、工厂模式、Protocol 抽象等设计模式，确保业务模块与基础设施解耦，支持多租户架构的资源隔离。

## 架构设计

### 设计原则

1. **依赖倒置**：framework 通过 Protocol 定义抽象接口，业务模块实现具体逻辑，避免反向依赖
2. **工厂模式**：所有外部资源访问（存储、队列、发布订阅、锁）通过工厂函数创建，支持配置驱动切换实现
3. **多租户隔离**：支持数据库、缓存、存储三层物理隔离，租户上下文自动传播
4. **模块化设计**：业务模块通过 `ModuleDescriptor` 声明式注册，框架自动扫描、加载、管理依赖

### 模块分层

```text
┌─────────────────────────────────────────────────────────┐
│                     业务模块层                           │
│                   iam / demo / tenant                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Framework 基础设施层                   │
├─────────────────────────────────────────────────────────┤
│  clients  │  tenant  │  module  │  common  │  configs  │
├─────────────────────────────────────────────────────────┤
│    cache    │   database   │   storage   │   queue     │
├─────────────────────────────────────────────────────────┤
│     lock    │    pubsub    │   schemas   │   utils     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    核心抽象层 (core/)                     │
│           Protocol 定义 / 工厂接口 / 常量                │
└─────────────────────────────────────────────────────────┘
```

## 子模块详细设计

### 1. configs - 配置管理

**职责**：统一配置加载、环境变量覆盖、配置模型定义

**核心组件**：
- `Settings`：全局配置模型，包含 server、database、redis、storage、lock 等子配置
- `YamlConfigLoader`：YAML 配置文件加载器
- `init_settings()`：初始化配置并注册到全局上下文

**设计特点**：
- 支持 YAML 文件 + 环境变量覆盖
- Pydantic 模型校验，类型安全
- 单例模式，全局唯一配置实例

**使用示例**：
```python
from framework.configs import init_settings, get_settings

# 初始化配置
settings = init_settings("config/development.yaml")

# 获取配置
print(settings.server.port)  # 8000
print(settings.database.url)  # postgresql+asyncpg://...
```

### 2. database - 数据库层

**职责**：SQLAlchemy 基础模型、Mixin、类型、事件监听、引擎池管理

#### 2.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `BaseModel` | `core/base.py` | 基础模型，包含 `id`、`created_at`、`updated_at` 字段 |
| `ModuleBase` | `core/module_base.py` | 模块级基类，支持 PostgreSQL Schema 隔离 |
| `DatabaseEnginePool` | `core/engine_pool.py` | 租户引擎池管理，LRU 缓存、惰性加载 |
| `TenantMixin` | `mixins/tenant.py` | 租户隔离 Mixin，自动填充 `tenant_id` |
| `AuditMixin` | `mixins/audit.py` | 审计 Mixin，记录 `created_by`、`updated_by` |
| `TreeNodeMixin` | `mixins/tree.py` | 树结构 Mixin，支持层级关系查询 |
| `ActiveRecordMixin` | `mixins/active_record.py` | 活动记录模式，提供 CRUD 快捷方法 |

#### 2.2 DatabaseEnginePool 设计

**核心功能**：
- 默认引擎 + 租户独立引擎管理
- LRU 缓存策略，最大缓存 50 个引擎
- 空闲超时自动回收（默认 30 分钟）
- 惰性加载，按需创建引擎

**使用示例**：
```python
from framework.database.core.engine_pool import DatabaseEnginePool

engine_pool = DatabaseEnginePool(max_engines=50, idle_timeout=1800)

# 初始化默认引擎
await engine_pool.init_default_engine(database_url)

# 获取租户引擎（租户独立数据库）
engine = await engine_pool.get_engine("tenant_001", tenant_db_config)

# 获取会话
async with engine_pool.session("tenant_001") as session:
    users = await session.execute(select(User))
```

#### 2.3 事件监听

| 事件类 | 文件 | 职责 |
|--------|------|------|
| `TenantEventListener` | `events/tenant.py` | 自动填充 `tenant_id`，防止跨租户数据访问 |
| `AuditEventListener` | `events/audit.py` | 自动填充审计字段 `created_by`、`updated_by` |

#### 2.4 查询拦截器

| 拦截器 | 文件 | 职责 |
|--------|------|------|
| `TenantQueryInterceptor` | `interceptors/query.py` | 自动注入 `WHERE tenant_id = :current_tenant` 过滤条件 |
| `SoftDeleteInterceptor` | `interceptors/query.py` | 自动过滤 `deleted_at IS NULL` 条件 |

### 3. cache - 缓存层

**职责**：Redis 工具、租户缓存管理、租户 Redis 工具

#### 3.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `RedisUtil` | `redis_util.py` | Redis 基础工具类，封装常用操作 |
| `TenantCacheManager` | `tenant_cache_manager.py` | 租户缓存管理器，支持独立 DB 隔离 |
| `TenantRedisUtil` | `tenant_redis_util.py` | 租户级 Redis 操作，自动添加租户前缀 |

#### 3.2 TenantCacheManager 设计

**隔离策略**：
- **物理隔离**：租户独立 Redis DB（DB 0-15）
- **逻辑隔离**：默认 DB + Key 前缀（`{tenant_id}:{key}`）

**使用示例**：
```python
from framework.cache.tenant_cache_manager import init_cache_manager, get_cache_manager

# 初始化缓存管理器
cache_manager = init_cache_manager(default_redis_client)

# 注册租户独立 Redis DB
cache_manager.register_tenant_db("tenant_001", db=1)

# 获取租户客户端
client = cache_manager.get_client("tenant_001")
await client.set("key", "value")
```

#### 3.3 TenantRedisUtil 设计

**核心功能**：
- 自动从 `TenantContext` 获取租户 ID
- 自动添加租户前缀到 Key、Queue、Channel、Lock
- 支持 `skip_tenant=True` 跳过租户隔离（管理员场景）

**前缀格式**：
```python
# Key 前缀
"{tenant_id}:{key}"

# 队列前缀
"{tenant_id}:queue:{queue_name}"

# 频道前缀
"{tenant_id}:channel:{channel_name}"

# 锁前缀
"{tenant_id}:lock:{lock_key}"
```

### 4. storage - 存储层

**职责**：对象存储工厂、多厂商实现、租户存储管理

#### 4.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `StorageProvider` | `core/storage.py` | 存储抽象 Protocol |
| `MinioStorage` | `impl/minio.py` | MinIO 实现 |
| `AliyunOssStorage` | `impl/aliyun.py` | 阿里云 OSS 实现 |
| `TencentCosStorage` | `impl/tencent.py` | 腾讯云 COS 实现 |
| `TenantStorageManager` | `tenant_storage_manager.py` | 租户存储桶路由管理 |
| `TenantStorageUtil` | `tenant_storage.py` | 租户级存储操作辅助函数 |

#### 4.2 TenantStorageManager 设计

**隔离策略**：
- **物理隔离**：租户独立 Bucket
- **逻辑隔离**：默认 Bucket + 路径前缀（`{tenant_id}/{path}`）

**使用示例**：
```python
from framework.storage.tenant_storage_manager import init_storage_manager
from framework.storage.tenant_storage import tenant_storage_upload, tenant_storage_download

# 初始化存储管理器
storage_manager = init_storage_manager(default_storage, "default-bucket")

# 注册租户存储桶
storage_manager.register_bucket("tenant_001", "tenant-001-bucket")

# 租户级存储操作（自动添加租户前缀）
await tenant_storage_upload("my-bucket", "files/report.pdf", file_data)
content = await tenant_storage_download("my-bucket", "files/report.pdf")
```

### 5. queue - 队列层

**职责**：消息队列工厂、Redis Stream 实现、任务队列、任务执行器

#### 5.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `QueueProvider` | `core/queue.py` | 队列抽象 Protocol |
| `RedisStreamQueue` | `impl/redis.py` | Redis Stream 实现 |
| `TenantTaskQueue` | `task_queue.py` | 租户感知的任务队列 |
| `TenantTaskExecutor` | `task_executor.py` | 租户感知的任务执行器 |
| `TaskMessage` | `task_message.py` | 任务消息封装 |

#### 5.2 TenantTaskQueue 设计

**核心功能**：
- 任务入队自动携带租户 ID
- 队列名称自动添加租户前缀
- 支持 Redis Stream 持久化

**使用示例**：
```python
from framework.queue.task_queue import enqueue_task

# 入队任务（自动携带当前租户上下文）
task_id = await enqueue_task(
    task_type="send_email",
    payload={"to": "user@example.com", "subject": "欢迎"},
    queue_name="email-queue"
)
```

#### 5.3 TenantTaskExecutor 设计

**执行流程**：
1. 从队列消费任务消息
2. 解析 `tenant_id`，加载租户信息
3. 设置租户上下文
4. 执行任务处理器
5. 清理租户上下文（即使任务异常也会清理）

**使用示例**：
```python
from framework.queue.task_executor import register_task_handler, TenantTaskExecutor

# 注册任务处理器
async def send_email_handler(payload: dict) -> None:
    # 发送邮件逻辑
    ...

register_task_handler("send_email", send_email_handler)

# 执行任务
success = await TenantTaskExecutor.execute(task_message)
```

### 6. pubsub - 发布订阅层

**职责**：发布订阅工厂、Handler 抽象、Redis 实现

#### 6.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `PubSubProvider` | `core/pubsub.py` | 发布订阅抽象 Protocol |
| `RedisPubSub` | `impl/redis.py` | Redis Pub/Sub 实现 |
| `PubSubHandler` | `handler.py` | 消息处理器抽象 |

**使用示例**：
```python
from framework.pubsub import get_pubsub_provider

pubsub = get_pubsub_provider(settings.messaging)

# 发布消息
await pubsub.publish("user.created", {"user_id": "123"})

# 订阅频道
async def handle_user_created(message: dict) -> None:
    print(f"User created: {message['user_id']}")

await pubsub.subscribe("user.created", handle_user_created)
```

### 7. lock - 分布式锁层

**职责**：分布式锁工厂、Redis 实现、SQLAlchemy 实现

#### 7.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `LockProvider` | `core/lock.py` | 分布式锁抽象 Protocol |
| `RedisLock` | `impl/redis.py` | Redis 锁实现（基于 SETNX） |
| `SQLAlchemyLock` | `impl/sqlalchemy.py` | 数据库锁实现 |

**使用示例**：
```python
from framework.lock import get_lock_provider

lock_provider = get_lock_provider(settings.lock)

# 上下文管理器方式
async with lock_provider.acquire_context("order:123", ttl=30) as lock:
    if lock:
        # 获取锁成功，执行业务逻辑
        ...
    else:
        # 获取锁失败
        ...
```

### 8. tenant - 多租户层

**职责**：租户上下文管理、中间件、解析器、缓存、枚举、异常、Protocol

#### 8.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `TenantContext` | `context.py` | 租户上下文管理，基于 `contextvars` |
| `TenantMiddleware` | `middleware.py` | FastAPI 中间件，自动解析租户标识 |
| `TenantResolver` | `resolver.py` | 租户解析器，支持 Header、Subdomain、Path 解析 |
| `TenantCache` | `cache.py` | 租户信息缓存 |
| `TenantProvider` | `protocols.py` | 租户提供者 Protocol（依赖倒置） |

#### 8.2 TenantContext 设计

**核心功能**：
- 基于 `contextvars` 实现请求级隔离
- 提供便捷函数：`get_tenant_id()`、`get_tenant_code()`、`get_tenant_name()`
- 支持嵌套上下文，自动清理

**使用示例**：
```python
from framework.tenant import (
    set_current_tenant,
    get_tenant_id,
    clear_tenant_context,
    SimpleTenant,
)

# 设置当前租户
tenant = SimpleTenant(id="tenant_001", code="T001", name="测试租户")
set_current_tenant(tenant)

# 获取租户信息
tenant_id = get_tenant_id()  # "tenant_001"

# 清理上下文
clear_tenant_context()
```

#### 8.3 TenantMiddleware 设计

**中间件流程**：
1. 从请求解析租户标识（Header / Subdomain / Path）
2. 调用 `TenantProvider` 获取租户信息
3. 设置租户上下文
4. 执行请求处理
5. 清理租户上下文

**配置示例**：
```python
from framework.tenant import TenantMiddleware, TenantResolver

# 配置解析器
resolver = TenantResolver(
    header_name="X-Tenant-Id",
    resolver_type="header"
)

# 添加中间件
app.add_middleware(TenantMiddleware, resolver=resolver)
```

#### 8.4 租户资源隔离策略

| 资源 | 物理隔离 | 逻辑隔离 |
|------|---------|---------|
| 数据库 | 独立 Database / Schema | `tenant_id` 字段过滤 |
| 缓存 | 独立 Redis 实例 | Key 前缀 `{tenant_id}:{key}` |
| 存储 | 独立 Bucket / 服务 | 路径前缀 `{tenant_id}/{path}` |
| 队列 | 独立队列实例 | Key 前缀 `{tenant_id}:queue:{name}` |
| 发布订阅 | 独立消息实例 | 频道前缀 `{tenant_id}:channel:{name}` |

### 9. 资源配置详解

租户资源配置通过 `TenantInfo` 协议的属性传递，支持灵活的物理隔离和逻辑隔离策略。配置定义在 `framework.tenant.protocols` 模块。

#### 9.1 TenantCacheConfig - 缓存配置

**字段说明：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | `str` | `""` | Redis 主机地址，配置后启用物理隔离 |
| `port` | `int` | `6379` | Redis 端口 |
| `password` | `str` | `""` | Redis 密码（已解密） |
| `db` | `int` | `0` | Redis DB 编号（0-15），配置非 0 启用 DB 隔离 |
| `prefix` | `str` | `""` | 键前缀（可选） |

**隔离策略：**

1. **物理隔离**：配置 `host` 后，使用独立的 Redis 实例
2. **DB 隔离**：配置 `db` 为非 0 值，使用同一实例的不同 DB
3. **前缀隔离**（默认）：不配置 `host` 和 `db`，自动添加 `{tenant_id}:{key}` 前缀

**使用示例：**

```python
from framework.tenant.protocols import TenantCacheConfig

# 物理隔离：独立 Redis 实例
cache_config = TenantCacheConfig(
    host="redis-tenant-001.example.com",
    port=6379,
    password="secret",
    db=0,
)

# DB 隔离：同一 Redis 实例的不同 DB
cache_config = TenantCacheConfig(
    db=3,  # 使用 DB 3
)

# 前缀隔离（默认行为）：无需配置，系统自动添加前缀
# TenantCacheManager 会自动处理
```

**管理器使用：**

```python
from framework.cache.tenant_cache_manager import get_cache_manager

cache_manager = get_cache_manager()

# 获取租户客户端（自动路由）
client = await cache_manager.get_client(
    tenant_id="tenant_001",
    config=cache_config,  # 传入租户的缓存配置
)

# 设置缓存（自动添加前缀或路由到正确实例）
await cache_manager.set("user:123", "data", config=cache_config)
```

#### 9.2 TenantStorageConfig - 存储配置

**字段说明：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `type` | `StorageType` | `MINIO` | 存储类型（MINIO / ALIYUN_OSS / TENCENT_COS） |
| `endpoint` | `str` | `""` | 存储服务端点，配置后启用物理隔离 |
| `access_key` | `str` | `""` | 访问密钥 |
| `secret_key` | `str` | `""` | 密钥（已解密） |
| `bucket` | `str` | `""` | 存储桶名称，配置后使用独立 Bucket |

**隔离策略：**

1. **物理隔离**：配置 `endpoint` 后，使用独立的存储服务
2. **Bucket 隔离**：配置 `bucket` 后，使用同一服务的独立 Bucket
3. **前缀隔离**（默认）：不配置 `endpoint` 和 `bucket`，自动添加 `{tenant_id}/{path}` 路径前缀

**使用示例：**

```python
from framework.tenant.protocols import TenantStorageConfig

# 物理隔离：独立 MinIO 服务
storage_config = TenantStorageConfig(
    endpoint="minio-tenant-001.example.com:9000",
    access_key="tenant001_key",
    secret_key="tenant001_secret",
    bucket="tenant-001-bucket",
)

# Bucket 隔离：同一 MinIO 服务的不同 Bucket
storage_config = TenantStorageConfig(
    bucket="tenant-001-bucket",
)

# 前缀隔离（默认行为）：无需配置，系统自动添加路径前缀
# TenantStorageManager 会自动处理
```

**管理器使用：**

```python
from framework.storage.tenant_storage_manager import get_storage_manager

storage_manager = get_storage_manager()

# 上传文件（自动路由到正确存储桶/服务）
url = await storage_manager.upload(
    path="documents/report.pdf",
    data=file_bytes,
    tenant_id="tenant_001",
    config=storage_config,
)

# 下载文件
content = await storage_manager.download(
    path="documents/report.pdf",
    config=storage_config,
)
```

#### 9.3 TenantQueueConfig - 队列配置

**字段说明：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `type` | `QueueType` | `REDIS` | 队列类型（目前支持 REDIS） |
| `host` | `str` | `""` | 队列服务主机，配置后启用物理隔离 |
| `port` | `int` | `5672` | 队列服务端口 |
| `username` | `str` | `""` | 用户名 |
| `password` | `str` | `""` | 密码（已解密） |
| `vhost` | `str` | `"/"` | 虚拟主机（RabbitMQ） |

**隔离策略：**

1. **物理隔离**：配置 `host` 后，使用独立的队列实例
2. **前缀隔离**（默认）：不配置 `host`，自动添加 `{tenant_id}:queue:{name}` 前缀

**使用示例：**

```python
from framework.tenant.protocols import TenantQueueConfig

# 物理隔离：独立 Redis 队列实例
queue_config = TenantQueueConfig(
    host="redis-queue-001.example.com",
    port=6379,
    password="secret",
)

# 前缀隔离（默认行为）：无需配置，系统自动添加队列名前缀
# TenantQueueManager 会自动处理
```

**管理器使用：**

```python
from framework.queue.tenant_queue_manager import get_queue_manager

queue_manager = get_queue_manager()

# 发送消息到队列（自动路由）
message_id = await queue_manager.xadd(
    queue_name="email-queue",
    fields={"to": "user@example.com", "subject": "Hello"},
    tenant_id="tenant_001",
    config=queue_config,
)

# 消费消息
messages = await queue_manager.xreadgroup(
    groupname="email-workers",
    consumername="worker-1",
    queue_name="email-queue",
    config=queue_config,
)
```

#### 9.4 TenantPubSubConfig - 发布订阅配置

**字段说明：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `type` | `PubSubType` | `REDIS` | 发布订阅类型（目前支持 REDIS） |
| `host` | `str` | `""` | 消息服务主机，配置后启用物理隔离 |
| `port` | `int` | `6379` | 消息服务端口 |
| `username` | `str` | `""` | 用户名 |
| `password` | `str` | `""` | 密码（已解密） |

**隔离策略：**

1. **物理隔离**：配置 `host` 后，使用独立的消息实例
2. **前缀隔离**（默认）：不配置 `host`，自动添加 `{tenant_id}:channel:{name}` 频道前缀

**使用示例：**

```python
from framework.tenant.protocols import TenantPubSubConfig

# 物理隔离：独立 Redis PubSub 实例
pubsub_config = TenantPubSubConfig(
    host="redis-pubsub-001.example.com",
    port=6379,
    password="secret",
)

# 前缀隔离（默认行为）：无需配置，系统自动添加频道名前缀
# TenantPubSubManager 会自动处理
```

**管理器使用：**

```python
from framework.pubsub.tenant_pubsub_manager import get_pubsub_manager

pubsub_manager = get_pubsub_manager()

# 发布消息（自动路由到正确实例/频道）
subscriber_count = await pubsub_manager.publish(
    channel="user-events",
    message='{"event": "user_created", "user_id": "123"}',
    tenant_id="tenant_001",
    config=pubsub_config,
)

# 订阅频道
pubsub = await pubsub_manager.subscribe(
    channel="user-events",
    config=pubsub_config,
)
```

#### 9.5 配置传递方式

租户资源配置通过 `TenantInfo` 协议传递，业务模块实现 `TenantProvider` 协议时返回包含资源配置的租户信息：

```python
from framework.tenant.protocols import (
    TenantInfo,
    TenantCacheConfig,
    TenantStorageConfig,
)

class MyTenantInfo(TenantInfo):
    def __init__(self, tenant_data):
        self._data = tenant_data

    # 基础信息
    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def name(self) -> str:
        return self._data["name"]

    # 资源配置（可选）
    @property
    def cache(self) -> TenantCacheConfig | None:
        if self._data.get("cache_config"):
            return TenantCacheConfig(**self._data["cache_config"])
        return None

    @property
    def storage(self) -> TenantStorageConfig | None:
        if self._data.get("storage_config"):
            return TenantStorageConfig(**self._data["storage_config"])
        return None
```

#### 9.6 隔离策略选择指南

| 场景 | 推荐策略 | 说明 |
|------|---------|------|
| 中小租户、成本敏感 | 前缀隔离 | 共享资源，最低成本，依赖代码过滤 |
| 中型租户、需要一定隔离 | DB/Bucket 隔离 | 同一实例的逻辑隔离，中等成本 |
| 大型企业租户、高安全要求 | 物理隔离 | 独立资源实例，最高安全，成本最高 |
| 混合场景 | 按需配置 | VIP 租户物理隔离，普通租户逻辑隔离 |

### 10. clients - 内部客户端层

**职责**：模块间 HTTP 调用客户端封装

#### 10.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `InnerHttpClient` | `inner_http_client.py` | 内部服务 HTTP 客户端 |
| `TenantClient` | `tenant_client.py` | 租户服务客户端 |
| `IamClient` | `iam_client.py` | IAM 服务客户端 |

#### 10.2 InnerHttpClient 设计

**核心功能**：
- 支持单体模式和微服务模式切换
- 自动服务发现（微服务模式）
- 统一超时、重试、熔断策略
- 支持 Pydantic 模型自动序列化/反序列化

**使用示例**：
```python
from framework.clients import InnerHttpClient

client = InnerHttpClient(
    base_url="http://localhost:8000",
    service_name="iam",
    timeout=30.0
)

# GET 请求
response = await client.get("/inner/v1/users/123")

# 获取列表（自动反序列化）
users = await client.get_list("/inner/v1/users", UserVo)

# POST 请求
result = await client.post("/inner/v1/users", json={"username": "test"})
```

### 11. common - 通用组件层

**职责**：通用上下文、异常、响应、枚举、单例、异常处理器

#### 11.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `ctx` | `ctx.py` | 请求上下文管理（`tenant_id`、`user_id` 等） |
| `exceptions` | `exceptions.py` | 自定义异常体系（`AppException`、`NotFoundError` 等） |
| `enums` | `enums.py` | 通用枚举（`ErrorCode`、`HttpStatus`） |
| `singleton` | `singleton.py` | 单例装饰器 |
| `exception_handler` | `exception_handler.py` | FastAPI 全局异常处理器、统一错误响应格式（`error_response`） |

#### 11.2 异常体系设计

```python
class AppException(Exception):
    """应用异常基类"""
    def __init__(self, message: str, code: int = 500, data: Any = None):
        self.message = message
        self.code = code
        self.data = data

class NotFoundError(AppException):
    """资源不存在异常"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} not found: {identifier}", code=404)

class ValidationError(AppException):
    """验证失败异常"""
    def __init__(self, message: str, data: Any = None):
        super().__init__(message, code=422, data=data)
```

#### 11.3 统一响应格式

```python
# 成功响应
{
    "code": 200,
    "message": "success",
    "data": {...}
}

# 错误响应
{
    "code": 404,
    "message": "User not found: 123",
    "data": null
}
```

### 12. module - 模块系统

**职责**：模块动态加载、注册中心、依赖解析

#### 12.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `ModuleDescriptor` | `descriptor.py` | 模块描述符 Protocol |
| `ModuleRegistry` | `registry.py` | 模块注册中心（单例） |
| `load_modules()` | `loader.py` | 模块扫描与加载函数 |

#### 12.2 ModuleDescriptor Protocol

```python
class ModuleDescriptor(Protocol):
    """模块描述符"""
    
    @property
    def name(self) -> str:
        """模块名称"""
        ...
    
    @property
    def schema(self) -> str:
        """数据库 Schema 名称"""
        ...
    
    @property
    def dependencies(self) -> list[str]:
        """依赖模块列表"""
        ...
    
    def get_base(self) -> type:
        """获取模块的 SQLAlchemy Base 类"""
        ...
    
    def get_routers(self) -> list[APIRouter]:
        """获取模块的 FastAPI 路由列表"""
        ...
```

#### 12.3 模块加载流程

```python
from framework.module import load_modules, get_registry
from pathlib import Path

# 1. 扫描并加载模块
modules = load_modules(
    Path("src"),
    module_names=["iam", "demo", "tenant"]
)

# 2. 获取注册中心
registry = get_registry()

# 3. 获取模块信息
iam_module = registry.get_module("iam")
print(iam_module.name)  # "iam"
print(iam_module.dependencies)  # ["tenant"]

# 4. 获取所有模块的 Base 类
bases = registry.get_all_bases()

# 5. 获取所有模块的配置 Schema
schemas = registry.get_all_schemas()
```

### 13. utils - 工具层

**职责**：加密、JWT、Session、字符串、时间、JSON、树形结构、启动计时器等工具

#### 13.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `crypto` | `crypto.py` | AES-256-GCM 加密解密工具 |
| `jwt` | `jwt.py` | JWT 令牌生成与验证 |
| `session` | `session.py` | Session 管理工具 |
| `string_util` | `string_util.py` | 字符串处理工具（驼峰转换、随机字符串等） |
| `time_util` | `time_util.py` | 时间处理工具（时区转换、格式化等） |
| `json_util` | `json_util.py` | JSON 序列化工具（支持 datetime、UUID 等） |
| `tree_util` | `tree_util.py` | 树形结构构建工具 |
| `startup_timer` | `startup_timer.py` | 启动计时器，记录各阶段耗时 |
| `enum_util` | `enum_util.py` | 枚举工具类 |
| `dictionary_util` | `dictionary_util.py` | 字典工具类 |
| `property_util` | `property_util.py` | 属性描述符工具 |
| `log_util` | `log_util.py` | 日志格式化工具 |
| `file_util` | `file_util.py` | 文件处理工具 |

#### 13.2 StartupTimer 设计

**核心功能**：
- 记录应用启动各阶段耗时
- 支持阶段排序
- 打印格式化启动摘要

**使用示例**：
```python
from framework.utils.startup_timer import StartupTimer

timer = StartupTimer("AI 助手平台")

with timer.phase("数据库初始化", order=1) as phase:
    phase.details["连接池大小"] = "10"
    # 初始化数据库
    ...

with timer.phase("模块加载", order=2) as phase:
    phase.details["模块数量"] = "3"
    # 加载模块
    ...

timer.print_summary(
    modules=["iam", "demo", "tenant"],
    address="http://localhost:8000",
    docs_path="/docs"
)
```

**输出示例**：
```
──────────────────────────────────────
AI 助手平台 启动完成！
总启动耗时: 2.345 秒
启动阶段耗时:
  阶段1 (数据库初始化): 0.567秒
    - 连接池大小: 10
  阶段2 (模块加载): 1.234秒
    - 模块数量: 3
完成时间: 2026-06-01 10:30:00
🔌 已加载模块: 3 个
   - iam
   - demo
   - tenant

访问地址: http://localhost:8000
API 文档: http://localhost:8000/docs
──────────────────────────────────────
```

## 设计决策与最佳实践

### 1. 依赖倒置原则

**问题**：framework 需要租户信息，但不能依赖业务模块

**解决方案**：
- 在 `framework.tenant.protocols` 定义 `TenantProvider` Protocol
- 业务模块（如 `tenant`）实现 `TenantProvider`
- 应用启动时通过 `register_tenant_provider()` 注册实现
- framework 通过 `get_tenant_provider()` 获取实现并调用

### 2. 多租户隔离策略

**物理隔离 vs 逻辑隔离**：

| 维度 | 物理隔离 | 逻辑隔离 |
|------|---------|---------|
| 数据安全 | 高（独立资源） | 中（依赖过滤条件） |
| 成本 | 高（资源独立） | 低（共享资源） |
| 运维复杂度 | 高 | 低 |
| 适用场景 | 大型企业租户 | 中小租户 |

**混合策略**：
- 关键租户使用物理隔离（独立数据库、独立 Bucket）
- 普通租户使用逻辑隔离（共享资源 + 前缀隔离）

### 3. 异步优先

**原则**：所有 I/O 操作使用 `async/await`，避免阻塞事件循环

**实现**：
- 数据库：SQLAlchemy 2.0 AsyncSession
- Redis：redis.asyncio.Redis
- HTTP：httpx.AsyncClient
- 存储：MinIO Python SDK（async wrapper）

### 4. 错误处理策略

**异常分类**：
- `AppException`：业务异常，返回错误响应
- `ValidationError`：验证异常，返回 422
- `NotFoundError`：资源不存在，返回 404
- `TenantError`：租户相关异常

**全局异常处理器**：
```python
from framework.common.exception_handler import (
    app_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

### 5. 配置管理最佳实践

**配置层次**：
1. 默认配置（代码中定义）
2. YAML 配置文件
3. 环境变量覆盖
4. 命令行参数（最高优先级）

**敏感信息处理**：
- 使用环境变量传递敏感信息（数据库密码、密钥等）
- 支持 `.env` 文件（开发环境）
- 生产环境使用密钥管理服务（Vault、AWS Secrets Manager）

## 扩展指南

### 添加新的存储实现

1. 在 `core/storage.py` 实现 `StorageProvider` Protocol
2. 在 `storage/impl/` 创建实现文件（如 `s3.py`）
3. 在 `storage/factory.py` 添加工厂方法
4. 在 `configs/settings.py` 添加配置项

### 添加新的队列实现

1. 在 `core/queue.py` 实现 `QueueProvider` Protocol
2. 在 `queue/impl/` 创建实现文件（如 `rabbitmq.py`）
3. 在 `queue/factory.py` 添加工厂方法
4. 在 `configs/settings.py` 添加配置项

### 添加新的 Mixin

1. 在 `database/mixins/` 创建 Mixin 文件
2. 提供默认字段和行为方法
3. 在 `database/__init__.py` 导出
4. 更新 CLAUDE.md 文档

## 测试策略

### 单元测试

- 路径：`tests/framework/unit/`
- 原则：隔离外部依赖，使用 Mock
- 覆盖：工具类、Mixin、工厂函数

### 集成测试

- 路径：`tests/framework/integration/`
- 依赖：Docker Compose 启动 PostgreSQL、Redis、MinIO
- 覆盖：数据库操作、缓存操作、存储操作

## 总结

Framework 模块是 Python 后端的基石，通过以下设计确保系统的可维护性和可扩展性：

1. **模块化设计**：清晰的职责划分，低耦合高内聚
2. **依赖倒置**：业务模块实现 Protocol，framework 调用抽象接口
3. **多租户支持**：三层资源隔离，支持物理隔离和逻辑隔离混合策略
4. **异步优先**：全面采用 async/await，提升并发性能
5. **可扩展性**：工厂模式、Protocol 抽象，易于添加新实现