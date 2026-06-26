# AI Platform Backend

AI 助手平台后端服务，基于 FastAPI 构建的**模块化单体架构**。

## 功能特点

### 核心能力

- **基于 FastAPI 的 Web 服务**：高性能异步 Web 框架
- **模块化单体架构**：模块级 Schema 隔离，支持独立部署
- **模块动态加载**：通过 `module.py` 声明，支持按需加载
- **基于 LangChain / LangGraph**：AI 智能体框架
- **统一返回结构**：RESTful API 设计，统一的 JSON 消息体格式
- **完善的错误处理**：全局异常处理和自动错误追踪

### 数据与存储

- **数据库集成**：SQLAlchemy 2.0 + Alembic + PostgreSQL（pgvector）
- **模块级 Schema 隔离**：每个模块拥有独立的 PostgreSQL schema
- **缓存支持**：Redis 用于高性能缓存
- **分层配置**：基于 YAML 的多环境配置系统

## 技术栈

- **后端框架**：FastAPI 0.115
- **ORM**：SQLAlchemy 2.0
- **数据库**：PostgreSQL + pgvector
- **缓存**：Redis
- **验证**：Pydantic 2.10
- **迁移工具**：Alembic 1.14
- **测试**：pytest + pytest-asyncio

## 环境要求

- Python 3.12
- PostgreSQL 14+（可选）
- Redis 6+（可选）
- uv（Python 包管理器）

## 项目结构

```text
server/python/
├── manage.py                   # 统一管理脚本
├── src/                        # 源码目录
│   ├── demo/                   # Demo 业务模块
│   │   ├── module.py           # 模块声明
│   │   ├── app.py              # 独立应用工厂
│   │   ├── controllers/        # API 控制器
│   │   ├── services/           # 业务逻辑层
│   │   ├── models/             # 数据库模型（demo schema）
│   │   ├── schemas/            # Pydantic 模型
│   │   ├── migrations/         # 数据库迁移
│   │   ├── listeners/          # 消息监听器
│   │   └── tasks/              # 定时任务
│   ├── iam/                    # IAM 身份认证模块
│   │   ├── module.py           # 模块声明
│   │   ├── app.py              # 独立应用工厂
│   │   ├── controllers/        # API 控制器
│   │   ├── services/           # 业务逻辑层
│   │   ├── models/             # 数据库模型（iam schema）
│   │   ├── schemas/            # Pydantic 模型
│   │   ├── migrations/         # 数据库迁移
│   │   ├── initializers/       # 初始化器
│   │   └── middlewares/        # 中间件
│   ├── framework/              # 基础设施模块
│   │   ├── module/             # 模块系统（动态加载、注册中心）
│   │   ├── configs/            # 配置管理
│   │   ├── cache/              # Redis 缓存
│   │   ├── database/           # 数据库组件（含 module_base.py）
│   │   ├── storage/            # 对象存储
│   │   ├── queue/              # 消息队列
│   │   ├── pubsub/             # 发布订阅
│   │   ├── lock/               # 分布式锁
│   │   └── tenant/             # 租户模型
│   ├── application_web.py      # FastAPI 应用入口（动态模块装配）
│   ├── application_task.py     # 任务调度器入口
│   ├── application_listener.py # 消息监听器入口
├── tests/                      # 测试目录
│   ├── framework/              # Framework 模块测试
│   │   └── unit/module/        # 模块系统单元测试
│   ├── iam/                    # IAM 模块测试
│   └── README.md               # 测试说明
└── config/                     # 配置目录（引用共享配置）
```

## 模块架构

项目采用**模块化单体架构**，支持从单体到微服务的平滑过渡：

### 架构特性

| 特性 | 说明 |
| --- | --- |
| Schema 隔离 | 每个模块拥有独立的 PostgreSQL schema（如 `iam.users`） |
| 独立迁移 | 每个模块拥有独立的 `alembic_version` 表 |
| 动态加载 | 通过 `module.py` 声明，支持 `--module` 参数按需加载 |
| 独立部署 | 每个模块可通过 `app.py` 提供独立应用工厂 |

### 模块列表

| 模块 | Schema | 说明 |
| --- | --- | --- |
| framework | - | 基础设施模块：配置、缓存、存储、队列等 |
| tenant | `tenant` | 租户模块：资源配置、模块（角色、菜单、权限）、租户、插件等 |
| iam | `iam` | 身份认证模块：组织、角色、用户、菜单、权限管理 |
| demo | `demo` | 业务演示模块：知识库管理示例 |

### 模块结构

每个业务模块包含：

| 文件/目录 | 说明 |
| --- | --- |
| `module.py` | 模块声明，实现 `ModuleDescriptor` 协议 |
| `app.py` | 独立应用工厂，支持单模块部署 |
| `models/` | 数据库模型（使用 `create_module_base(schema)`） |
| `migrations/` | 数据库迁移（配置 `version_table_schema`） |
| `controllers/` | API 控制器 |
| `services/` | 业务逻辑层 |

### 开发新模块

```bash
# 1. 创建模块目录
mkdir -p src/my_module/{models,controllers,services,schemas,migrations/versions}

# 2. 创建 models/__init__.py
cat > src/my_module/models/__init__.py << 'EOF'
from framework.database import create_module_base, create_base_model

Base = create_module_base("my_module")
BaseModel = create_base_model(Base)
EOF

# 3. 创建 module.py
cat > src/my_module/module.py << 'EOF'
class MyModule:
    @property
    def name(self) -> str:
        return "my_module"

    @property
    def schema(self) -> str:
        return "my_module"

    @property
    def dependencies(self) -> list[str]:
        return []

    def get_base(self) -> type:
        from my_module.models import Base
        return Base

    def get_routers(self) -> list[tuple]:
        return []

    def get_seeds(self) -> dict:
        return {}

    def get_task_setup(self) -> tuple | None:
        return None

    def get_listener_setup(self) -> tuple | None:
        return None
EOF

# 4. 创建 migrations/env.py
# 参考 iam/migrations/env.py 或 demo/migrations/env.py
```

## 快速开始

### 安装

```bash
# 安装依赖
uv sync

# 同步所有依赖组
uv sync --all-groups

# 安装 LangChain 依赖（可选）
uv sync --group langchain

# 仅 graphrag 相关测试
uv sync --group graphrag
```

### 配置

配置文件统一放置在 `server/config/` 目录下：

```bash
# 复制配置文件
cp server/config/application-local.yml.example server/config/application-local.yml

# 编辑配置文件，配置数据库和 Redis 连接
vim server/config/application-local.yml
```

### 运行

项目提供统一的管理脚本 `manage.py`：

```bash
# 启动 Web 服务（加载所有模块）
uv run python manage.py runserver

# 启动 Web 服务（按需加载模块）
uv run python manage.py runserver --module iam,demo

# 指定主机/端口
uv run python manage.py runserver --host 0.0.0.0 --port 8080

# 启动开发模式（热重载）
uv run python manage.py runserver --reload

# 启动定时任务调度器（指定模块）
uv run python manage.py runtask --module demo

# 启动监听器服务（指定模块）
uv run python manage.py runlistener --module demo
```

### 访问

- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc：[http://localhost:8000/redoc](http://localhost:8000/redoc)
- 健康检查：[http://localhost:8000/health](http://localhost:8000/health)

## 开发指南

详细开发指南见 [CLAUDE.md](CLAUDE.md)。

### 代码风格

```bash
# 格式化代码
uv run format-code

# 仅检查
uv run format-code --check-only
```

### 自动迁移及初始化数据

应用启动时支持自动执行数据库迁移和种子数据初始化，通过配置控制行为。

#### 配置说明

| 环境 | 配置文件 | `auto_migrate` | 行为 |
| --- | --- | --- | --- |
| 开发环境 | `application-local.yml` | `true` | 启动时自动运行迁移 |
| 生产环境 | `application-prod.yml` | `false` | 禁用自动迁移，需手动执行 |
| 默认 | `application.yml` | `false` | 默认禁用 |

配置示例：

```yaml
# application-local.yml
sqlalchemy:
  url: "postgresql+asyncpg://admin:password@127.0.0.1:5432/ai_platform"
  echo: false
  auto-migrate: true  # 开发环境开启自动迁移
  pool:
    size: 20
    max-overflow: 30
```

#### 启动流程

```
Phase 1: 数据库迁移验证
├── 检查 schema 是否存在
├── 检查 alembic_version 表是否存在
├── auto_migrate=true  → 自动创建 schema 并运行迁移
└── auto_migrate=false → 提示手动运行迁移命令

Phase 2: 模块定义同步
├── 创建模块记录（tenant.modules）
├── 同步菜单定义（iam.menus）
├── 同步权限定义（iam.permissions）
├── 同步角色定义（iam.roles）
└── 同步全局角色（sysAdmin、normalUser）

Phase 3: 种子数据初始化
├── 资源配置（database_configs、cache_configs 等）
├── 全局角色（sysAdmin、normalUser）
├── 默认租户（tenant.tenants）
├── 模块分配（tenant.tenant_modules）
├── 默认组织（iam.organizations）
└── 默认用户（iam.users）

Phase 4: 数据完整性验证
└── 检查关键数据是否存在
```

#### 使用方式

**开发环境（auto_migrate: true）**

```bash
# 直接启动，自动完成所有初始化
uv run python manage.py runserver
```

启动日志示例：

```
[Phase 1] Auto Migration
  - [tenant] 自动创建 Schema
  - [tenant] 迁移执行成功
  - [tenant] 自动迁移完成
  - ... (iam, ai, demo 同样)

[Phase 2] Module Sync
  - 模块 tenant 同步完成
  - 全局角色同步完成

[Phase 3] Seeds
  - 已创建默认资源配置
  - 已创建租户: 默认租户
  - 已创建用户: admin

[Phase 4] Verification
  SUCCESS
```

**生产环境（auto_migrate: false）**

```bash
# 1. 手动运行迁移
uv run python manage.py db migrate --all --yes

# 2. 启动服务（自动执行种子数据初始化）
uv run python manage.py runserver
```

启动日志示例：

```
[Phase 1] Migration Validation
  - 检测到迁移缺失: ['tenant', 'iam']
  - 请运行: uv run python manage.py db migrate --all --yes
  - 或在配置中设置 sqlalchemy.auto_migrate: true 自动运行迁移
```

#### 新增迁移和种子

| 类型 | 自动执行 | 说明 |
| --- | --- | --- |
| Migration | ✅（需 `auto_migrate: true`） | 新增迁移文件后，启动时自动执行 |
| Seed | ✅（始终） | 新增种子数据后，启动时自动执行（幂等检查） |

**新增迁移示例：**

```bash
# 创建新迁移文件
uv run python manage.py db makemigrations --module iam -m "add new feature"

# 开发环境：auto_migrate: true 启动时自动执行
# 生产环境：auto_migrate: false 手动运行 migrate 命令
```

**新增种子示例：**

```python
# src/iam/migrations/seeds/new_seed.py
async def run(*, dry_run: bool = False) -> int:
    """新增种子数据"""
    # 幂等检查：已存在则跳过
    existing = await session.execute(select(Model).where(...))
    if existing.scalar_one_or_none():
        return 0

    # 创建数据
    session.add(Model(...))
    await session.commit()
    return 1
```

```python
# src/iam/module.py - 注册种子
def get_seeds(self) -> dict[str, Callable]:
    from iam.migrations.seeds.new_seed import run as new_seed_run
    return {
        "new_seed": new_seed_run,
        # ... 其他种子
    }
```

#### 注意事项

| 场景 | 建议 |
| --- | --- |
| 开发环境 | 使用 `auto_migrate: true`，快速迭代 |
| 测试/CI 环境 | 使用 `auto_migrate: true`，自动化流程 |
| 生产环境 | 使用 `auto_migrate: false`，控制变更时机 |
| 多实例部署 | 确保只有一个实例执行迁移，或使用分布式锁 |

### 数据库迁移

项目采用模块化迁移架构，每个模块拥有独立的 PostgreSQL schema 和迁移版本表。

```bash
# 查看所有模块迁移状态
uv run python manage.py db current

# 执行指定模块迁移
uv run python manage.py db migrate --module iam

# 执行所有模块迁移
uv run python manage.py db migrate --all

# 预览迁移 SQL（不执行）
uv run python manage.py db migrate --sql --module iam

# 回退指定模块迁移
uv run python manage.py db downgrade --module iam

# 查看迁移历史
uv run python manage.py db history --module iam

# 创建新迁移
uv run python manage.py db makemigrations --module iam -m "描述"

# 重建模块 Schema（危险操作）
uv run python manage.py db rebuild --module iam
uv run python manage.py db rebuild --all
```

### 数据初始化

```bash
# 初始化所有模块的默认数据
uv run python manage.py seed

# 预览待初始化的数据（不写入）
uv run python manage.py seed --dry-run

# 初始化指定模块
uv run python manage.py seed --module iam
```

### 默认资源配置初始化

应用启动时，通过 `seed` 命令自动创建默认资源配置（如果不存在）：

- 从 `application.yml` 读取数据库（PostgreSQL）、缓存（Redis）、存储（MinIO/S3）、队列和发布订阅等配置
- 为每个配置类型创建默认记录，标记 `is_default=True`
- 敏感字段（密码、密钥等）使用 AES-256-GCM 加密存储
- 使用 PostgreSQL 部分唯一索引保证每种配置最多只有一条默认记录

创建租户时，如果未指定资源配置 ID，系统会自动关联默认配置：

```python
# 自动关联逻辑：tenant_service.create()
if db_config_id is None:
    default_db = await database_config_service.get_default_config(session)
    if default_db:
        db_config_id = default_db.id
```

默认配置支持通过管理 API 切换：将任意非默认配置设为 `is_default=True` 时，
原默认配置的标记将自动清除，保证同一类型配置始终只有一个默认值。

### 测试

详细测试说明见 [tests/README.md](tests/README.md)。

```bash
# 运行所有测试
uv run pytest

# 跳过慢测试
uv run pytest -m "not slow"
```

## 常见问题

### 数据库迁移问题

#### 问题 1：迁移失败 - schema 不存在

**现象**：首次运行迁移时报错 `schema "iam" does not exist`

**原因**：Alembic 在创建 `alembic_version` 表前，目标 schema 尚不存在

**解决**：在 `migrations/env.py` 的迁移上下文配置前确保 schema 存在：

```python
async with connectable.connect() as connection:
    from sqlalchemy import text
    await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}"))
    await connection.commit()
    await connection.run_sync(do_run_migrations)
```

参考：`src/iam/migrations/env.py`

#### 问题 2：模型创建失败导致事务回滚

**现象**：创建模型时报外键约束错误

**原因**：跨 schema 外键未指定完整的 `schema.table.column` 格式

**解决**：在模型定义中指定完整 schema：

```python
# 错误
ForeignKey("tenants.id", ondelete="CASCADE")

# 正确
ForeignKey("tenant.tenants.id", ondelete="CASCADE")
```

参考：`src/iam/models/role.py`

#### 问题 3：种子数据初始化失败

**现象**：执行 `seed` 命令时报外键验证错误

**原因**：SQLAlchemy ORM 对跨 schema 外键验证可能失败

**解决**：使用原生 SQL 插入数据：

```python
await session.execute(
    text("INSERT INTO iam.roles (...) VALUES (...)"),
    {...}
)
```

参考：`src/iam/migrations/seeds/iam_seed.py`

#### 问题 4：每次迁移重复删建外键

**现象**：每次运行迁移都会删除并重建相同的外键

**原因**：Alembic 自动生成的外键未指定 `referent_schema`

**解决**：在迁移脚本中手动创建跨 schema 外键：

```python
op.create_foreign_key(
    constraint_name="fk_roles_tenant_id",
    source_table="roles",
    referent_table="tenants",
    local_cols=["tenant_id"],
    remote_cols=["id"],
    source_schema="iam",
    referent_schema="tenant",  # 关键！
    ondelete="CASCADE"
)
```
