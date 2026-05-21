# CLAUDE.md

本文件为 Claude Code 在 Python 后端项目中工作时提供指导。

## 项目概述

Python 后端使用 FastAPI + SQLAlchemy 2.0 构建，提供 AI 助手平台演示。项目采用基于 uv 的单包结构，支持 MVC 分层架构。

**核心技术栈：**

- 框架：FastAPI, SQLAlchemy 2.0, Alembic
- AI框架：langchain 1.3.0, langgraph 1.2.0
- 数据库：PostgreSQL (pgvector), Redis
- 验证：Pydantic 2.10
- 测试：pytest, pytest-asyncio, pytest-mock

## 项目结构

```text
server/python/
├── manage.py               # 统一管理脚本
├── src/                    # 源码目录
│   ├── demo/               # Demo 业务模块
│   │   ├── controllers/    # API 控制器
│   │   ├── services/       # 业务逻辑层
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── migrations/     # 数据库迁移
│   │   │   ├── versions/   # 迁移版本文件
│   │   │   └── seeds/      # 数据初始化脚本
│   │   └── ...
│   ├── iam/                # IAM 身份认证模块
│   │   ├── controllers/    # API 控制器
│   │   ├── services/       # 业务逻辑层
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── migrations/     # 数据库迁移
│   │   ├── initializers/   # 初始化器
│   │   └── middlewares/    # 中间件
│   ├── framework/          # 基础设施框架
│   │   ├── configs/        # 配置管理
│   │   ├── cache/          # Redis 缓存
│   │   ├── database/       # 数据库组件
│   │   ├── storage/        # 对象存储
│   │   ├── queue/          # 消息队列
│   │   ├── pubsub/         # 发布订阅
│   │   ├── lock/           # 分布式锁
│   │   └── tenant/         # 租户模型
│   ├── application_web.py      # FastAPI 应用入口
│   ├── application_task.py     # 任务调度器入口
│   ├── application_listener.py # 消息监听器入口
│   └── run.py                  # Web 服务器启动入口
├── tests/                  # 测试目录
├── config/                 # 配置目录（符号链接到 server/config/）
├── pyproject.toml          # 项目配置
├── alembic.ini             # Alembic 配置
├── pytest.ini              # pytest 配置
└── .ruff.toml              # Ruff 配置
```

## 功能模块

| 模块 | 说明 | 目录 |
|------|------|------|
| demo | 业务演示模块：知识库管理示例 | src/demo/ |
| iam | 身份认证模块：租户、用户、权限管理 | src/iam/ |
| framework | 基础设施：配置、缓存、存储、队列、锁、租户 | src/framework/ |

详细文档：[src/CLAUDE.md](src/CLAUDE.md)

## 管理命令

项目提供统一的管理脚本 `manage.py`，类似 Django 的 manage.py 风格。

```bash
# 查看帮助
uv run python manage.py --help

# 启动 Web 服务器
uv run python manage.py runserver

# 指定主机/端口启动
uv run python manage.py runserver --host 0.0.0.0 --port 8080

# 开发模式（热重载）
uv run python manage.py runserver --reload

# 启动定时任务调度器
uv run python manage.py runtask

# 启动监听器服务
uv run python manage.py runlistener
```

## 数据库迁移

项目采用模块化迁移架构，使用 `manage.py db` 子命令管理。

### 迁移命令

```bash
# 查看当前数据库版本
uv run python manage.py db current

# 执行迁移
uv run python manage.py db migrate

# 预览迁移 SQL（不执行）
uv run python manage.py db migrate --sql

# 回滚迁移
uv run python manage.py db downgrade

# 查看迁移历史
uv run python manage.py db history

# 创建新迁移
uv run python manage.py db makemigrations -m "add user tables"
```

### 指定数据库连接

所有 `db` 命令支持 `-d/--database-url` 选项：

```bash
uv run python manage.py db -d "postgresql+asyncpg://user:pass@host:5432/dbname" migrate
```

### 迁移文件规范

迁移文件位于 `src/demo/migrations/versions/`，命名格式：`YYYYMMDD_NNN_description.py`

```python
"""add user tables

Revision ID: user_001
Revises: 001_tenant
Create Date: 2026-05-21

"""
from alembic import op
import sqlalchemy as sa

revision = "user_001"
down_revision = "001_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", ...)


def downgrade() -> None:
    op.drop_table("users")
```

## 数据初始化

数据初始化脚本位于 `src/demo/migrations/seeds/`，支持幂等执行和 dry-run 预览。

### 初始化命令

```bash
# 初始化所有模块的默认数据
uv run python manage.py seed

# 预览待初始化的数据（不写入数据库）
uv run python manage.py seed --dry-run

# 初始化指定模块
uv run python manage.py seed --module tenant
```

### 添加新模块

**步骤 1：创建迁移文件**

```bash
uv run python manage.py db makemigrations -m "add user tables"
```

**步骤 2：创建种子脚本** `src/demo/migrations/seeds/user_seed.py`

```python
"""用户模块数据初始化"""

from sqlalchemy import select
from framework.database.core.engine import get_session
from demo.models.user import User


async def run(*, dry_run: bool = False) -> int:
    """初始化用户数据"""
    async with get_session() as session:
        # 检查是否已存在
        result = await session.execute(select(User).limit(1))
        if result.scalar():
            print("    用户数据已存在，跳过初始化")
            return 0

        if dry_run:
            print("    [DRY-RUN] 将创建默认用户")
            return 1

        # 创建默认用户
        user = User(username="admin", email="admin@example.com")
        session.add(user)
        await session.commit()

        print("    已创建默认用户")
        return 1
```

**步骤 3：注册模块** 在 `src/demo/migrations/seeds/__init__.py`

```python
from demo.migrations.seeds.user_seed import run as user_run

SEED_MODULES["user"] = user_run
```

## 配置管理

采用 Spring Boot 风格的分层配置，配置文件统一在 `server/config/` 目录。

```bash
# 本地开发配置
cp server/config/application-local.yml.example server/config/application-local.yml
```

**环境选择：** 通过 `PYTHON_SERVICE_ENV` 环境变量指定，默认 `local`。

## 代码质量标准

- **Linter/格式化**：Ruff
- **行宽**：88 字符
- **Python 版本**：3.12
- **类型标注**：统一使用 `Mapped[...]` 声明式注解

## 详细文档

- **开发指南**：[src/CLAUDE.md](src/CLAUDE.md)
- **测试指南**：[tests/CLAUDE.md](tests/CLAUDE.md)

## 环境要求

- Python 3.12+
- PostgreSQL 14+
- Redis 6+
- uv (Python 包管理器)

## License

Copyright © 2025 Moles. All Rights Reserved.
