# Framework 开发指南

## 概述

Framework 模块提供统一的基础设施组件，支持多技术栈（Python 优先实现）。

## 模块结构

```
framework/
├── config/         # 统一配置模块
├── cache/          # Redis 缓存模块
├── core/           # 核心接口定义
├── common/         # 通用组件
├── storage/        # 存储实现
├── queue/          # 队列实现
├── lock/           # 分布式锁
├── pubsub/         # 发布订阅
├── database/       # 数据库组件
├── tenant/         # 租户模型
└── utils/          # 工具函数
```

## 快速开始

### 配置加载

```python
from framework.config import init_settings, get_settings

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
from framework.config import get_settings

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
from framework.config import get_settings

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
