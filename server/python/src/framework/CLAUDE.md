# Framework 开发指南

## 概述

Framework 模块提供统一的基础设施组件，支持多技术栈（Python 优先实现）。

## 模块结构

```
framework/
├── config/         # 统一配置模块
├── cache/          # Redis 缓存模块
│   └── tenant_cache_manager.py  # 租户缓存管理器
├── core/           # 核心接口定义
├── common/         # 通用组件
├── storage/        # 存储实现
│   └── tenant_storage_manager.py # 租户存储管理器
├── queue/          # 队列实现
├── lock/           # 分布式锁
├── pubsub/         # 发布订阅
├── database/       # 数据库组件
│   └── core/engine_pool.py       # 数据库引擎池
├── tenant/         # 租户模型
└── utils/          # 工具函数
    └── crypto.py   # AES-256-GCM 加密工具
```

## 快速开始

### 配置加载

```python
from framework.configs import init_settings, get_settings

# 初始化配置
settings = init_settings("path/to/config")

# 访问配置
print(settings.server.port)
print(settings.redis.single.host)
```

### Redis 缓存

```python
from framework.cache.redis_util import RedisUtil

# 初始化
await RedisUtil.init(redis_config)

# 基础操作
await RedisUtil.set("key", "value", ttl=60)
value = await RedisUtil.get("key")
await RedisUtil.delete("key")

# 健康检查
is_healthy = await RedisUtil.health_check()
```

### 对象存储

```python
from framework.storage import get_storage_provider
from framework.configs import get_settings

settings = get_settings()
storage = get_storage_provider(settings.oss)

# 上传文件
url = await storage.upload("bucket", "path/file.txt", file_bytes)

# 下载文件
data = await storage.download("bucket", "path/file.txt")

# 获取预签名 URL
url = await storage.get_presigned_url("bucket", "path/file.txt", 3600)
```

### 分布式锁

```python
from framework.lock import get_lock_provider
from framework.configs import get_settings

settings = get_settings()
lock_provider = get_lock_provider(settings.lock)

# 获取锁
lock = await lock_provider.acquire("resource_key", ttl=30)
if lock:
    try:
        # 执行业务逻辑
        pass
    finally:
        await lock_provider.release(lock)

# 使用上下文管理器
async with lock_provider.acquire_context("resource_key", ttl=30) as lock:
    if lock:
        # 执行业务逻辑
        pass
```

### 数据库模型

```python
from framework.database import Base, BaseModel, TenantMixin, AuditMixin

class User(BaseModel, TenantMixin, AuditMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False)
```

### 多租户物理资源隔离

Framework 提供三种资源管理器，支持租户级物理隔离：

#### DatabaseEnginePool - 数据库连接池管理

```python
from framework.database.core.engine_pool import get_engine_pool, get_tenant_session
from framework.tenant.protocols import TenantDatabaseConfig

# 初始化默认引擎
from framework.database.core.engine_pool import init_default_engine
init_default_engine("postgresql+asyncpg://user:pass@localhost:5432/default_db")

# 获取租户会话
config = TenantDatabaseConfig(
    host="localhost",
    port=5432,
    database="tenant_001_db",
    username="user",
    password="password",
)
async with get_tenant_session("tenant-001", config) as session:
    # 使用租户独立数据库
    result = await session.execute(select(User))
```

#### TenantStorageManager - 存储桶路由

```python
from framework.storage.tenant_storage_manager import get_storage_manager, init_storage_manager
from framework.tenant.protocols import TenantStorageConfig

# 初始化
init_storage_manager(default_storage, "default-bucket")

# 上传文件到租户独立存储桶
config = TenantStorageConfig(bucket="tenant-001-bucket")
url = await manager.upload("avatars/user.jpg", data, "tenant-001", config)

# 下载文件
data = await manager.download("avatars/user.jpg", "tenant-001", config)
```

#### TenantCacheManager - Redis DB 路由

```python
from framework.cache.tenant_cache_manager import get_cache_manager, init_cache_manager
from framework.tenant.protocols import TenantCacheConfig

# 初始化
init_cache_manager(default_redis_client)

# 使用租户独立 Redis DB
config = TenantCacheConfig(db=3)
client = await manager.get_client("tenant-001", config)
await manager.set("key", "value", "tenant-001", config)
```

### 敏感信息加密

```python
from framework.utils.crypto import encrypt, decrypt, generate_tenant_key

# 生成租户加密密钥
tenant_key = generate_tenant_key()

# 加密敏感信息（如数据库密码）
encrypted = encrypt("my_database_password")

# 解密
decrypted = decrypt(encrypted)
```

#### 加密配置

通过环境变量设置主密钥：

```bash
export TENANT_ENCRYPTION_MASTER_KEY="your_64_char_hex_key"
```

开发环境会自动生成临时密钥。

## 设计模式

### 核心接口（Protocol）

使用 Python Protocol 定义抽象接口：

```python
from typing import Protocol

class StorageProvider(Protocol):
    async def upload(self, bucket: str, name: str, data: bytes) -> str: ...
    async def download(self, bucket: str, name: str) -> bytes: ...
```

### 工厂模式

根据配置返回对应实现：

```python
def get_storage_provider(config: OssSettings) -> StorageProvider:
    match config.default_type:
        case "minio": return MinioStorage(config.minio)
        case "aliyun": return AliyunStorage(config.aliyun)
```

## 测试

所有测试位于 `tests/framework/` 目录：

```bash
# 运行所有测试
pytest tests/framework -v

# 运行特定模块测试
pytest tests/framework/cache -v
```

## 注意事项

1. 所有 Redis 操作通过 `RedisUtil` 类进行
2. 使用 Protocol 定义接口，支持类型检查
3. 配置支持环境变量覆盖
4. 仅支持单元测试，不做集成测试

## 模块依赖规则

**framework 模块是底层基础设施，禁止引用业务模块（demo、iam 等）。**

```text
✅ 正确的依赖方向：
demo ──────▶ framework
iam ───────▶ framework

❌ 禁止的依赖方向：
framework ──▶ demo
framework ──▶ iam
```

### 依赖倒置解决方案

如果 framework 需要业务模块的能力，使用以下方式：

1. **定义 Protocol 接口**：在 framework 中定义抽象接口
2. **业务模块实现 Protocol**：在 iam/demo 中实现接口
3. **应用启动时注入实现**：通过全局注册机制注入

示例：`framework/tenant/protocols.py` 的 `TenantProvider` 设计

```python
# framework/tenant/protocols.py
class TenantProvider(Protocol):
    async def get_tenant(self, tenant_id: str) -> TenantInfo | None: ...

# iam/services/tenant_provider_impl.py
class IamTenantProvider(TenantProvider):
    async def get_tenant(self, tenant_id: str) -> TenantInfo | None:
        # 具体实现...

# application_web.py
register_tenant_provider(iam_tenant_provider)
```
