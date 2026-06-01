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
| `cache/` | Redis 工具、租户缓存管理、租户 Redis 工具 |
| `clients/` | 内部 HTTP 客户端、租户客户端、IAM 客户端 |
| `common/` | 通用上下文、异常、响应、枚举、单例、异常处理器 |
| `configs/` | YAML 配置加载、环境变量覆盖、配置模型 |
| `core/` | 存储、队列、发布订阅、锁等 Protocol / 抽象接口、树结构常量 |
| `database/` | SQLAlchemy 基础模型、Mixin、类型、事件、拦截器、引擎池 |
| `lock/` | 分布式锁工厂与实现 |
| `module/` | 模块动态加载系统：`ModuleDescriptor` Protocol、`ModuleRegistry` 注册中心、模块扫描与依赖解析 |
| `pubsub/` | 发布订阅工厂、Handler 与 Redis 实现 |
| `queue/` | 队列工厂、Handler、Redis Stream 实现、任务队列、任务执行器 |
| `schemas/` | Pydantic VO 基类（含 TreeNodeVo、TreeNodeTreeVo） |
| `storage/` | 对象存储工厂、MinIO/OSS/腾讯云实现、租户存储管理 |
| `tenant/` | 租户模型、上下文、中间件、解析器、缓存、枚举、异常、Protocol |
| `utils/` | 加密、JWT、Session、字符串、时间、JSON、树形结构、启动计时器等工具 |

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
| 数据库 | `framework.database.core.engine_pool.DatabaseEnginePool` | 租户独立 Database / Engine / Session |
| 存储 | `framework.storage.tenant_storage_manager.TenantStorageManager` | 租户独立 Bucket |
| 缓存 | `framework.cache.tenant_cache_manager.TenantCacheManager` | 租户独立 Redis DB |

未配置租户专属资源时，使用默认资源和逻辑隔离策略。

## 核心组件用法

### 配置加载

```python
from framework.configs import get_settings, init_settings

settings = init_settings("path/to/config")
print(settings.server.port)
```

### 模块系统

```python
from framework.module import get_registry, load_modules
from pathlib import Path

# 加载模块
modules = load_modules(Path("src"), module_names=["iam", "demo"])

# 使用注册中心
registry = get_registry()
module = registry.get_module("iam")
all_modules = registry.get_all_modules()
```

模块必须实现 `ModuleDescriptor` Protocol，声明 `name`、`schema`、`dependencies`、`get_base()`、`get_routers()` 等接口。

### Redis 缓存

```python
from framework.cache.redis_util import RedisUtil

await RedisUtil.init(redis_config)
await RedisUtil.set("key", "value", ttl=60)
value = await RedisUtil.get("key")
```

### 租户缓存管理

```python
from framework.cache.tenant_cache_manager import init_cache_manager, get_cache_manager

# 初始化租户缓存管理器
cache_manager = init_cache_manager(default_redis_client)

# 注册租户独立 Redis DB
cache_manager.register_tenant_db("tenant_001", db=1)

# 获取租户 Redis 客户端
tenant_client = cache_manager.get_client("tenant_001")
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

### 数据库引擎池

```python
from framework.database.core.engine_pool import DatabaseEnginePool

# 创建引擎池
engine_pool = DatabaseEnginePool(max_engines=50, idle_timeout=1800)

# 初始化默认引擎
await engine_pool.init_default_engine(database_url)

# 获取租户引擎
engine = await engine_pool.get_engine(tenant_id, tenant_db_config)

# 获取会话
async with engine_pool.session(tenant_id) as session:
    ...
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

### 任务队列

```python
from framework.queue.task_queue import enqueue_task

# 入队任务（自动携带租户上下文）
task_id = await enqueue_task("send_email", {"to": "user@example.com"})

# 注册任务处理器
from framework.queue.task_executor import register_task_handler

async def send_email_handler(payload: dict) -> None:
    # 处理发送邮件逻辑
    ...

register_task_handler("send_email", send_email_handler)
```

### 内部 HTTP 客户端

```python
from framework.clients import InnerHttpClient

# 创建客户端
client = InnerHttpClient(
    base_url="http://localhost:8000",
    service_name="iam",
    timeout=30.0
)

# 调用内部服务
response = await client.get("/inner/v1/users/123")
users = await client.get_list("/inner/v1/users", UserVo)
```

### 租户存储管理

```python
from framework.storage.tenant_storage_manager import init_storage_manager, get_storage_manager

# 初始化存储管理器
storage_manager = init_storage_manager(default_storage, default_bucket)

# 注册租户存储桶
storage_manager.register_bucket("tenant_001", "tenant-001-bucket")

# 使用租户存储
from framework.storage.tenant_storage import tenant_storage_upload, tenant_storage_download

await tenant_storage_upload("my-bucket", "file.txt", file_data)
content = await tenant_storage_download("my-bucket", "file.txt")
```

### 租户上下文

```python
from framework.tenant import (
    TenantContext,
    get_tenant_id,
    get_tenant_code,
    set_current_tenant,
    clear_tenant_context,
)

# 设置当前租户
tenant_info = SimpleTenant(id="tenant_001", code="T001", name="测试租户")
set_current_tenant(tenant_info)

# 获取租户信息
tenant_id = get_tenant_id()
tenant_code = get_tenant_code()

# 清理上下文
clear_tenant_context()
```

### 依赖倒置

```python
from typing import Protocol

class TenantProvider(Protocol):
    async def get_tenant(self, tenant_id: str) -> TenantInfo | None: ...
```

业务模块实现 Protocol，应用启动时注册实现，framework 只依赖抽象。

### 启动计时器

```python
from framework.utils.startup_timer import StartupTimer

timer = StartupTimer("应用名称")

with timer.phase("数据库初始化", order=1):
    # 初始化数据库
    ...

with timer.phase("模块加载", order=2):
    # 加载模块
    ...

timer.print_summary(
    modules=["iam", "demo"],
    address="http://localhost:8000",
    docs_path="/docs"
)
```

## 测试

- 单元测试位于 `tests/framework/unit/`。
- 集成测试位于 `tests/framework/integration/`，可能依赖 Redis、PostgreSQL、MinIO。
- 详细测试约定见 [../../tests/framework/CLAUDE.md](../../tests/framework/CLAUDE.md)。

```bash
uv run pytest tests/framework/unit/ -v
uv run pytest tests/framework/integration/ -v
```