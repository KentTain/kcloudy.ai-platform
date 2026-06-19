# Design: 模块化单体架构重构

## Context

当前 Python 后端采用单进程架构，所有模块（`iam`、`demo`）的数据库表共享 `public` schema 和同一个 `alembic_version` 版本表。模块装配通过 `application_web.py` 等入口文件硬编码 `import` 实现，新增模块需要手动修改多个文件。

**约束条件**：
- 保持现有 API 端点路径不变
- 保持现有业务逻辑不变
- 支持 PostgreSQL 多 schema 特性
- 兼容现有 SQLAlchemy 2.0 代码风格

**利益相关者**：
- 后端开发团队
- 运维团队（部署配置）

## Goals / Non-Goals

**Goals:**

1. **数据库 Schema 隔离**：每个模块拥有独立的 PostgreSQL schema，包括独立的迁移版本表
2. **模块动态加载**：通过 `module.py` 声明模块信息，支持自动扫描和按需加载
3. **模块独立部署**：通过 `app.py` 提供完整应用工厂，支持单模块独立运行
4. **向后兼容**：现有 API 端点、业务逻辑保持不变

**Non-Goals:**

1. 不实现数据库物理隔离（每个模块独立数据库实例）
2. 不实现服务网格或复杂的微服务治理（仅支持简单 HTTP 调用）
3. 不改动前端代码
4. 不实现热插拔（模块需重启服务才能加载/卸载）

## Decisions

### Decision 1: 模块级 Base 工厂函数

**选择**：提供 `create_module_base(schema)` 工厂函数，每个模块调用创建带 schema 的 `DeclarativeBase`。

**备选方案**：
- **方案 A**：每个 Model 手动添加 `__table_args__ = {'schema': 'iam'}` — 放弃，容易遗漏，维护成本高
- **方案 B**：全局 Base + 运行时切换 schema — 放弃，SQLAlchemy 不支持动态 schema，且迁移生成复杂

**实现**：

```python
# framework/database/core/module_base.py

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime
from typing import Any
from sqlalchemy import String, DateTime, func

def create_module_base(schema: str) -> type[DeclarativeBase]:
    """为模块创建带 schema 的 DeclarativeBase"""
    class ModuleBase(AsyncAttrs, DeclarativeBase):
        metadata = MetaData(schema=schema)
    return ModuleBase

def create_base_model(module_base: type) -> type:
    """为模块创建 BaseModel"""
    class BaseModel(module_base):
        __abstract__ = True

        id: Mapped[str] = mapped_column(String(36), primary_key=True, comment="ID")
        created_at: Mapped[datetime] = mapped_column(
            DateTime, server_default=func.now(), comment="创建时间"
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
        )

        def to_dict(self) -> dict[str, Any]:
            return {
                column.name: getattr(self, column.name)
                for column in self.__table__.columns
            }
    return BaseModel
```

**每个模块的 models/__init__.py**：

```python
# iam/models/__init__.py
from framework.database import create_module_base, create_base_model

Base = create_module_base("iam")
BaseModel = create_base_model(Base)
```

### Decision 2: ModuleDescriptor 协议

**选择**：定义 `ModuleDescriptor` Protocol，模块通过 `module.py` 实现该协议。

**备选方案**：
- **方案 A**：使用装饰器注册 `@register_module` — 放弃，需要模块在被导入时执行，依赖隐式副作用
- **方案 B**：使用配置文件 (YAML/JSON) — 放弃，无法表达复杂对象（路由、中间件类），类型不安全

**实现**：

```python
# framework/module/descriptor.py

from typing import Protocol, Any, Callable
from fastapi import FastAPI

class ModuleDescriptor(Protocol):
    """模块声明协议"""

    @property
    def name(self) -> str:
        """模块名"""
        ...

    @property
    def schema(self) -> str:
        """PostgreSQL schema 名"""
        ...

    @property
    def dependencies(self) -> list[str]:
        """依赖的其他模块"""
        ...

    def get_base(self) -> type:
        """返回模块的 DeclarativeBase"""
        ...

    def get_routers(self) -> list[tuple]:
        """返回 [(router, prefix, tags), ...]"""
        ...

    def get_middlewares(self) -> list[type]:
        """返回中间件列表"""
        ...

    def get_lifespan_hooks(self) -> list[Callable]:
        """返回生命周期钩子"""
        ...

    def get_seeds(self) -> dict[str, Callable]:
        """返回 seed 注册表"""
        ...

    def get_task_setup(self) -> tuple | None:
        """返回 (setup_func, cleanup_func)"""
        ...

    def get_listener_setup(self) -> tuple | None:
        """返回 (setup_func, cleanup_func)"""
        ...
```

### Decision 3: 模块扫描与加载策略

**选择**：启动时扫描 `src/*/module.py`，根据 `--module` 参数过滤后加载。

**备选方案**：
- **方案 A**：预注册列表（在 manage.py 中硬编码模块名）— 放弃，新增模块仍需修改代码
- **方案 B**：使用 entry_points (setuptools) — 放弃，增加打包复杂度，不适合开发期迭代

**实现流程**：

```
manage.py runserver [--module X,Y]
         │
         ▼
┌─────────────────────────────────────┐
│ discover_modules(src_path)          │
│ 扫描 src/*/module.py                 │
│ 获取模块 descriptor                  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ filter_modules(modules, module_arg) │
│ 按 --module 参数过滤                 │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ resolve_dependencies(modules)       │
│ 拓扑排序确保依赖顺序                 │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ assemble_application(modules)       │
│ 创建 FastAPI app                     │
│ 注册路由、中间件、lifespan           │
└─────────────────────────────────────┘
```

### Decision 4: Alembic 多 Schema 迁移

**选择**：每个模块维护独立的 `migrations/env.py`，配置 `version_table_schema`。

**备选方案**：
- **方案 A**：单一 alembic 配置，多 version_table — 放弃，Alembic 不支持单配置多版本表
- **方案 B**：Flyway 等外部工具 — 放弃，放弃 SQLAlchemy autogenerate 能力

**实现**：

```python
# iam/migrations/env.py

from iam.models import Base

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="iam",  # 版本表在 iam schema
    )
```

**manage.py db 命令**：

```bash
python manage.py db makemigrations --module iam -m "add oauth"
python manage.py db migrate --module iam
python manage.py db migrate --all
```

### Decision 5: 跨模块调用策略

**选择**：单体模式使用本地函数调用，微服务模式使用 HTTP API。

**备选方案**：
- **方案 A**：统一 HTTP 调用（单体也走 HTTP）— 放弃，增加延迟和复杂度
- **方案 B**：消息队列异步调用 — 放弃，不适合同步查询场景

**实现**：

```python
# framework/module/client.py

class ModuleClient:
    """模块客户端，根据部署模式选择调用方式"""

    def __init__(self, module_name: str, base_url: str | None = None):
        self.module_name = module_name
        self.base_url = base_url  # 微服务模式下的服务 URL

    async def get_tenant(self, tenant_id: str) -> dict | None:
        if self.base_url:
            # 微服务模式：HTTP 调用
            return await self._http_get(f"{self.base_url}/api/v1/tenants/{tenant_id}")
        else:
            # 单体模式：本地调用
            from iam.services.tenant_service import TenantService
            return await TenantService.get_tenant(tenant_id)
```

### Decision 6: 重建迁移脚本

**选择**：提供 `db rebuild` 命令，按模块删除 schema 并重建。

**实现**：

```python
# manage.py

@db.command()
@click.option("--module", help="指定模块")
@click.option("--all", "all_modules", is_flag=True, help="重建所有模块")
@click.pass_context
def rebuild(ctx, module, all_modules):
    """重建数据库 Schema"""
    modules = resolve_target_modules(module, all_modules)

    for m in modules:
        # 1. DROP SCHEMA CASCADE
        session.execute(f"DROP SCHEMA IF EXISTS {m.schema} CASCADE")

    for m in modules:
        # 2. CREATE SCHEMA
        session.execute(f"CREATE SCHEMA {m.schema}")

    for m in modules:
        # 3. alembic upgrade head
        config = get_alembic_config(m.name)
        command.upgrade(config, "head")

    for m in modules:
        # 4. run seeds
        for seed_name, seed_func in m.get_seeds().items():
            await seed_func(dry_run=False)
```

## Risks / Trade-offs

### Risk 1: 迁移脚本的破坏性

**风险**：`db rebuild` 会删除所有数据，生产环境误操作将导致数据丢失。

**缓解措施**：
- 命令执行前强制确认（生产环境需额外验证）
- 命令默认仅允许在 `local` 环境执行
- 添加 `--dry-run` 选项预览操作

### Risk 2: 现有测试的大面积修改

**风险**：大量测试文件 import `from framework.database import BaseModel`，需要逐个修改。

**缓解措施**：
- 保留 `framework.database.BaseModel` 作为兼容别名（指向一个无 schema 的 Base）
- 但新增测试必须使用模块级 `BaseModel`
- 编写迁移脚本自动替换 import 语句

### Risk 3: 跨模块查询复杂度增加

**风险**：移除跨模块外键后，需要应用层保证一致性，查询复杂度增加。

**缓解措施**：
- 封装通用的跨模块查询工具函数
- 对于高频查询场景，考虑使用缓存（Redis）
- 文档化跨模块调用最佳实践

### Risk 4: Alembic 多分支迁移的复杂性

**风险**：每个模块独立迁移版本，可能遇到分支合并冲突。

**缓解措施**：
- 每个模块的迁移文件使用日期前缀命名（如 `20260525_001_*.py`）
- 避免多个开发者同时修改同一模块的迁移
- 提供 `db history --module` 命令查看特定模块的迁移历史

## Migration Plan

### Phase 1: 框架层准备（不破坏现有功能）

1. 新增 `framework/database/core/module_base.py`
2. 新增 `framework/module/` 目录及相关文件
3. 更新 `framework/database/__init__.py` 导出新函数

### Phase 2: 模块迁移（逐个模块）

以 `iam` 为例：

1. 修改 `iam/models/__init__.py` 使用新 Base
2. 修改 `iam/models/*.py` 的 import 路径
3. 新增 `iam/module.py`
4. 新增 `iam/app.py`
5. 重写 `iam/migrations/env.py`
6. 迁移 `iam/migrations/seeds/__init__.py`
7. 运行测试验证

### Phase 3: 启动层重构

1. 重写 `application_web.py`
2. 重写 `application_task.py`
3. 重写 `application_listener.py`
4. 重写 `manage.py`
5. 更新 `alembic.ini` 或废弃（每个模块自己管理配置）

### Phase 4: 数据库重建与验证

1. 执行 `python manage.py db rebuild --all`
2. 验证所有 API 端点正常
3. 验证所有测试通过

### Phase 5: 清理与文档

1. 移除旧的 `demo/migrations/seeds/__init__.py`（已迁移到 iam）
2. 更新 `CLAUDE.md` 文档
3. 添加迁移指南文档

## Open Questions

1. **framework 是否需要自己的 schema？** 当前 framework 没有业务表，暂不需要。如果未来添加全局配置表，可考虑 `public` schema 或新增 `framework` schema。

2. **alembic.ini 如何处理？** 可以废弃，每个模块在 `migrations/` 目录下维护自己的 `alembic.ini`，或由 manage.py 动态生成配置。

3. **生产环境如何平滑迁移？** 当前为演示项目，直接重建数据库可接受。若未来需要平滑迁移，需编写数据迁移脚本。
