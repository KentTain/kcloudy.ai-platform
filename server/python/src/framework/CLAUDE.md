# Framework 开发指南

本文件为 Claude Code 在 `src/framework/` 基础设施模块中工作时提供指导。

## 模块定位

Framework 是 Python 后端的底层基础设施模块，提供配置、缓存、数据库、存储、队列、发布订阅、分布式锁、多租户和通用工具能力。

**依赖边界：** framework 禁止引用业务模块（如 `demo`、`iam`）。业务模块可以依赖 framework；framework 如需业务能力，必须通过 Protocol、注册器或启动期注入实现依赖倒置。

```text
demo / iam ──▶ framework
framework ──X──▶ demo / iam
```

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `configs/` | YAML 配置加载、环境变量覆盖、配置模型 |
| `cache/` | Redis 工具与租户缓存管理 |
| `common/` | 通用上下文、异常、响应、枚举 |
| `core/` | 存储、队列、发布订阅、锁等 Protocol / 抽象接口、树结构常量 |
| `database/` | SQLAlchemy 基础模型、Mixin（含 TreeNodeMixin）、类型、事件、引擎池 |
| `schemas/` | Pydantic VO 基类（含 TreeNodeVo、TreeNodeTreeVo） |
| `lock/` | 分布式锁工厂与实现 |
| `pubsub/` | 发布订阅工厂、Handler 与 Redis 实现 |
| `queue/` | 队列工厂、Handler 与 Redis Stream 实现 |
| `storage/` | 对象存储工厂与 MinIO、阿里云 OSS、腾讯云实现 |
| `tenant/` | 租户模型、上下文与资源隔离协议 |
| `utils/` | 加密、JWT、Session、字符串、时间、JSON、树形结构等工具 |

## 开发规则

- 抽象能力优先定义在 `core/` 或 `tenant/protocols.py`，具体实现放在对应组件目录。
- 根据配置选择实现时使用工厂函数，避免调用方直接依赖具体实现类。
- 数据库模型继承 framework 提供的基类和 Mixin，字段使用 SQLAlchemy 2.0 的 `Mapped[...]` / `mapped_column(...)` 写法。
- Redis、存储、队列、发布订阅、锁等外部资源访问应通过 framework 封装入口，不在业务模块重复封装底层客户端。
- 处理多租户资源时，优先使用租户级管理器：数据库引擎池、租户存储管理器、租户缓存管理器。
- 敏感租户配置（如数据库密码、租户密钥）使用 AES-256-GCM 加密工具处理，主密钥来自 `TENANT_ENCRYPTION_MASTER_KEY`。

## 多租户物理资源隔离

Framework 支持按租户切换物理资源：

| 资源 | 管理入口 | 隔离方式 |
| --- | --- | --- |
| 数据库 | `framework.database.core.engine_pool` | 租户独立 Database / Engine / Session |
| 存储 | `framework.storage.tenant_storage_manager` | 租户独立 Bucket |
| 缓存 | `framework.cache.tenant_cache_manager` | 租户独立 Redis DB |

未配置租户专属资源时，使用默认资源和逻辑隔离策略。

## 典型用法

### 配置加载

```python
from framework.configs import get_settings, init_settings

settings = init_settings("path/to/config")
print(settings.server.port)
```

### Redis 缓存

```python
from framework.cache.redis_util import RedisUtil

await RedisUtil.init(redis_config)
await RedisUtil.set("key", "value", ttl=60)
value = await RedisUtil.get("key")
```

### 分布式锁

```python
from framework.lock import get_lock_provider

lock_provider = get_lock_provider(settings.lock)
async with lock_provider.acquire_context("resource_key", ttl=30) as lock:
    if lock:
        ...
```

### 数据库模型

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from framework.database import AuditMixin, BaseModel, TenantMixin

class User(BaseModel, TenantMixin, AuditMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), nullable=False)
```

### 树结构模型

```python
from framework.database import BaseModel, TreeNodeMixin

class Department(BaseModel, TreeNodeMixin):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    @classmethod
    def tree_name_field(cls) -> str:
        return "name"

# 使用 TreeNodeMixin 内置方法
dept = await Department.create_node(session, {"name": "研发部"})
child = await Department.create_node(session, {"name": "前端组", "parent_id": dept.id})
tree = Department.build_tree(await Department.list_nodes(session))
```

### 依赖倒置

```python
from typing import Protocol

class TenantProvider(Protocol):
    async def get_tenant(self, tenant_id: str) -> TenantInfo | None: ...
```

业务模块实现 Protocol，应用启动时注册实现，framework 只依赖抽象。

## 测试

- 单元测试位于 `tests/framework/unit/`。
- 集成测试位于 `tests/framework/integration/`，可能依赖 Redis、PostgreSQL、MinIO。
- 详细测试约定见 [../../tests/framework/CLAUDE.md](../../tests/framework/CLAUDE.md)。

```bash
uv run pytest tests/framework/unit/ -v
uv run pytest tests/framework/integration/ -v
```
