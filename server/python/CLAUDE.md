# Python 后端指南

本文件为 Claude Code 在 `server/python/` Python 后端项目中工作时提供指导。

## 项目定位

Python 后端使用 FastAPI + SQLAlchemy 2.0 构建，是 AI Platform 的 Python 技术栈实现。项目采用 **模块化单体架构**，支持模块独立部署。

## 架构特性

- **模块级 Schema 隔离**：每个业务模块拥有独立的 PostgreSQL schema
- **模块动态加载**：通过 `module.py` 声明模块信息，支持按需加载
- **模块独立部署**：每个模块可通过 `app.py` 提供独立应用工厂

## 技术栈

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| ORM / 迁移 | SQLAlchemy 2.0、Alembic |
| 配置 / 校验 | Pydantic 2.x、YAML 配置 |
| AI 示例 | LangChain、LangGraph、MCP 示例 |
| 数据服务 | PostgreSQL（含 pgvector）、Redis、MinIO |
| 测试 | pytest、pytest-asyncio、pytest-mock |
| 代码质量 | Ruff |

## 模块导航

| 模块 | 定位 | Schema | 详细文档 |
|------|------|--------|----------|
| framework | 基础设施模块 | - | [src/framework/CLAUDE.md](src/framework/CLAUDE.md) |
| tenant | 租户管理模块 | tenant | [src/tenant/CLAUDE.md](src/tenant/CLAUDE.md) |
| iam | 身份认证与权限模块 | iam | [src/iam/CLAUDE.md](src/iam/CLAUDE.md) |
| ai | AI 能力模块 | ai | [src/ai/CLAUDE.md](src/ai/CLAUDE.md) |
| demo | AI 助手平台演示模块 | demo | [src/demo/CLAUDE.md](src/demo/CLAUDE.md) |

## 依赖边界

```
demo / iam / ai ──▶ framework
demo / iam ──▶ tenant
framework ──X──▶ demo / iam / tenant
```

- 业务模块可以依赖 `framework`
- `framework` 禁止依赖业务模块
- 可复用基础能力优先放入 `framework`

## 模块结构规范

每个业务模块必须包含：

| 文件 | 用途 |
|------|------|
| `module.py` | 模块声明，实现 `ModuleDescriptor` 协议 |
| `app.py` | 独立应用工厂，支持单模块部署 |
| `models/__init__.py` | 使用 `create_module_base(schema)` 创建模块 Base |
| `models/__init__.py` | 使用 `create_base_model(Base)` 创建数据模型基类 BaseModel |
| `migrations/env.py` | 配置 `version_table_schema` |

## 核心命令

```bash
# 重建模块 Schema（危险操作）
uv run python manage.py db rebuild --module iam
uv run python manage.py db rebuild --all

# 数据库迁移
uv run python manage.py db migrate --module iam
uv run python manage.py db migrate --all

# 数据初始化
uv run python manage.py seed

# 启动后端 API 服务
uv run python manage.py runserver
uv run python manage.py runserver --module iam,demo

# 运行测试
uv run pytest
uv run pytest tests/demo/ -v
```

## 开发约束

- Python 版本：3.12+
- ORM 字段：使用 SQLAlchemy 2.0 `Mapped[...]` / `mapped_column(...)`
- 模块模型：使用 `create_module_base(schema)` 创建模块级 Base
- 数据模型基类：使用 `create_base_model(Base)` 创建数据模型基类 BaseModel
- mixins类：按需使用 framework 框架 `server\python\src\framework\database\mixins` 下 mixins类 `ActiveRecordMixin、TenantMixin、TreeNodeMixin、AuditMixin、PropertyMixin`
- 异步测试：使用 `pytest.mark.asyncio`
- API 路由：遵循 `/{模块}/{类型}/v1/{功能}` 格式

## 数据库自动迁移及初始化数据

应用启动时支持自动执行数据库迁移和种子数据初始化，通过配置控制行为。

### RBAC 模块定义与同步

#### 各模块：定义 RBAC 元数据

每个业务模块（iam、tenant、ai、demo 等）通过 `get_module_definition()` 声明菜单、权限、角色：

```python
# src/{module}/module.py
from framework.module.definition import ModuleDefinition, MenuDef, PermissionDef, RoleDef

def get_module_definition() -> ModuleDefinition:
    return ModuleDefinition(
        code="iam",
        name="身份认证与权限",
        menus=[
            MenuDef(code="users", name="用户管理", path="/iam/users", icon="users"),
        ],
        permissions=[
            PermissionDef(code="iam:user:read", name="查看用户", resource="user", action="read"),
        ],
        default_roles=[
            RoleDef(code="admin", name="管理员", permissions=["iam:user:read", "iam:user:write"]),
        ],
    )
```

#### 框架：同步到模块定义层

应用启动时，`framework.module.sync_service.sync_module()` 将各模块的定义同步到 `tenant` schema：

| 表名 | 说明 |
|------|------|
| `tenant.module_menus` | 模块菜单定义 |
| `tenant.module_permissions` | 模块权限定义 |
| `tenant.module_roles` | 模块角色定义 |
| `tenant.module_role_permissions` | 角色权限关联 |
| `tenant.module_menu_permissions` | 菜单权限关联 |

#### IAM：同步到租户实例层

租户分配模块时，`iam.services.module_sync_service.sync_module_assigned()` 将模块定义复制到租户实例层：

| 模块定义层 (tenant schema) | 租户实例层 (iam schema) | 关联字段 |
|---------------------------|------------------------|---------|
| `module_menus` | `iam.menus` | `ref_id` |
| `module_permissions` | `iam.permissions` | `ref_id` |
| `module_roles` | `iam.roles` | `ref_id` |
| `module_role_permissions` | `iam.role_permissions` | — |

同步流程：
1. 从 `tenant.module_*` 读取模块定义
2. 创建租户实例记录，设置 `tenant_id` 和 `ref_id`
3. 通过 `ref_id` 实现幂等同步
4. 同步角色权限和菜单权限关联

**注意**：`tenant` 模块的菜单不同步到 `iam.menus`，由 tenant 模块自行管理。

### 配置说明

| 环境 | 配置文件 | `auto_migrate` | 行为 |
| --- | --- | --- | --- |
| 开发环境 | `application-local.yml` | `true` | 启动时自动运行迁移 |
| 生产环境 | `application-prod.yml` | `false` | 禁用自动迁移，需手动执行 |
| 默认 | `application.yml` | `false` | 默认禁用 |

## Service 层开发规范

### 分层职责

| 层 | 职责 | 禁止事项 |
|---|------|---------|
| Controller | 路由定义、参数校验、响应封装 | ❌ 数据组装逻辑、❌ 多 Service 调用 |
| Service | 业务逻辑、事务边界、数据聚合 | ❌ HTTP 相关处理 |
| Model | 数据存储、ORM 映射 | ❌ 业务逻辑 |

### Controller 简化原则

Controller 应只调用一个 Service 聚合方法并返回响应：

```python
# ✅ 推荐：一行调用
@router.get("/users/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    user_detail = await user_service.get_user_detail(user_id)
    if not user_detail:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ORJSONResponse(content={"code": 200, "data": user_detail.model_dump()})

# ❌ 禁止：多 Service 调用 + 手动组装
@router.get("/users/me")
async def get_current_user(user_id: str):
    user = await user_service.get_by_id(user_id)
    roles = await user_roles_service.get_user_roles(user_id)
    permissions = await permission_check_service.get_user_permissions(user_id)
    # ... 手动组装 30+ 行代码
```

### 跨模块调用

| 场景 | 方式 | 示例 |
|------|------|------|
| 同模块 Service | 直接导入 | `from iam.services.role_service import user_role_service` |
| 跨模块 Service | 通过模块入口 | `from tenant.services.tenant_service import tenant_service` |

## Session 使用规范

### 依赖注入模式（必须）

所有模块必须使用依赖注入模式获取数据库 Session，禁止在 Service 层内部创建 Session。

### Controller 层

Controller 通过 FastAPI Depends 注入 Session：

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from framework.database.dependencies import get_db_session

@router.get("/users")
async def list_users(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    users = await user_service.list_users(session)
    return ORJSONResponse(content={"code": 200, "data": users})
```

### Service 层

Service 方法接收 Session 参数，禁止内部创建：

```python
class UserService:
    # ✅ 正确：接收 session 参数
    async def list_users(self, session: AsyncSession) -> list[User]:
        result = await session.execute(select(User))
        return list(result.scalars().all())

    # ❌ 禁止：内部创建 session
    async def list_users(self) -> list[User]:
        async with async_session() as session:  # 禁止
            ...
```

### Listener 层

Listener 使用 `get_listener_session()` 获取 Session：

```python
from framework.database.dependencies import get_listener_session

class MyHandler:
    async def handle(self, message: dict) -> None:
        TenantContext.set_tenant_id(message["tenant_id"])
        async with get_listener_session() as session:
            await my_service.process(session, message)
```

### Task 层

Task 使用 `get_task_session()` 获取 Session：

```python
from framework.database.dependencies import get_task_session

async def my_task():
    async with get_task_session() as session:
        await my_service.cleanup(session)
```

### 废弃的 `async_session`

`async_session` 代理已废弃，仅保留向后兼容。新代码禁止使用。

## Schema 层开发规范

### 基类使用规范

**所有业务模块（iam、tenant、ai、demo）的 Schema 类必须继承 `framework.schemas.BaseModel` 或其子类。**

```python
# ✅ 推荐：使用 framework 提供的基类
from framework.schemas import BaseModel

class UserResponse(BaseModel):
    id: str
    username: str
    # 无需手动配置，已自动包含 from_attributes=True 等
```

**禁止直接继承 `pydantic.BaseModel`：**

```python
# ❌ 禁止：直接使用 pydantic 原生基类
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 冗余配置
    id: str
    username: str
```

### 基类选择指南

| 场景 | 使用基类 | 示例 |
|------|---------|------|
| 普通 Schema | `framework.schemas.BaseModel` | `UserResponse`, `UserCreate` |
| 非分页查询 | `framework.schemas.BaseQuery` | `UserQuery` |
| 分页查询 | `framework.schemas.BasePaginatedQuery` | `UserPaginatedQuery` |
| 树形响应 | `framework.schemas.TreeNodeVo` | `OrganizationTreeResponse` |
| 树形嵌套响应 | `framework.schemas.TreeNodeTreeVo` | `MenuTreeResponse` |

### framework.schemas.BaseModel 的优势

继承 `framework.schemas.BaseModel` 自动获得以下配置：

```python
model_config = ConfigDict(
    from_attributes=True,      # 自动从 ORM 模型转换
    populate_by_name=True,     # 支持别名填充
    use_enum_values=True,      # 枚举序列化为值
    validate_default=True,     # 验证默认值
    str_strip_whitespace=True, # 字符串自动去空格
    extra="ignore",            # 忽略额外字段
)
```

无需手动配置 `model_config = ConfigDict(from_attributes=True)`。

### 禁止冗余配置

如果 Schema 类继承 `framework.schemas.BaseModel`，禁止重复配置已包含的选项：

```python
# ❌ 禁止：冗余配置
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 已包含，冗余
    id: str
    username: str

# ✅ 正确：仅配置额外选项
class StrictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 仅额外配置
    id: str
```

### 导入语句规范

必须从 `framework.schemas` 导入基类：

```python
# ✅ 推荐
from framework.schemas import BaseModel
from framework.schemas import BaseModel, BaseQuery, BasePaginatedQuery

# ✅ 也可接受
from framework.schemas.base import BaseModel

# ❌ 禁止（业务模块）
from pydantic import BaseModel
```

### 豁免场景

以下场景可豁免使用 `framework.schemas.BaseModel`：

1. **`ai_plugin/sdk/*`**：独立插件 SDK，保持零依赖
2. **第三方库集成接口**：需在代码注释中说明原因

```python
# ai_plugin/sdk/schemas/model.py - 豁免
from pydantic import BaseModel  # ✅ 允许：独立 SDK

class ModelUsage(BaseModel):
    """模型使用统计基类"""
    pass
```

### 类型注解

使用 `from __future__ import annotations` 支持前向引用：

```python
from __future__ import annotations
from typing import TYPE_CHECKING

from framework.schemas import BaseModel

if TYPE_CHECKING:
    from iam.models import User


class UserResponse(BaseModel):
    id: str
    username: str
```

### 复杂转换方法

对于复杂转换，Schema 类可提供 `from_entity()` 类方法：

```python
from framework.schemas import BaseModel

class ModelItem(BaseModel):
    id: str
    name: str

    @classmethod
    def from_entity(cls, provider: str, model: "ProviderModel") -> "ModelItem":
        return cls(
            id=f"{provider}/{model.model}",
            name=model.model,
            description=model.label.zh_Hans or model.label.en_US,
        )
```

**转换方法禁止事项：**

- ❌ 禁止在转换方法中执行数据库查询
- ❌ 禁止在转换方法中进行业务规则验证
- ❌ 禁止在转换方法中产生副作用

## 测试

测试文件位于 `tests/` 目录，详见 [tests/CLAUDE.md](tests/CLAUDE.md)。

## 环境要求

- Python 3.12+
- uv
- PostgreSQL 14+
- Redis 6+
- MinIO（对象存储相关功能需要）

详细使用示例、跨 Schema 外键处理、常见问题见 [README.md](README.md)。
