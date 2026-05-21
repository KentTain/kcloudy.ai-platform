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
├── src/                       # 源码目录
│   ├── demo/                  # Demo 业务模块
│   │   ├── controllers/       # API 控制器
│   │   ├── services/          # 业务逻辑层
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── migrations/        # 数据库迁移
│   │   └── seeds/             # 数据初始化脚本
│   └── framework/             # 基础设施框架
├── tests/                     # 测试目录
│   ├── demo/                  # Demo 模块测试
│   └── framework/             # Framework 模块测试
├── config/                    # 配置目录（符号链接到 server/config/）
├── scripts/                   # 开发脚本
│   ├── migrate_db.py          # 数据库迁移脚本
│   └── seed_data.py           # 数据初始化入口
├── pyproject.toml             # 项目配置
├── alembic.ini                # Alembic 配置
├── pytest.ini                 # pytest 配置
└── .ruff.toml                 # Ruff 配置
```

## 功能模块

| 模块 | 说明 | 详细文档 |
|------|------|----------|
| demo | 业务演示模块：API 控制器、服务层、数据模型 | [src/CLAUDE.md](src/CLAUDE.md) |
| framework | 基础设施：配置、缓存、存储、队列、锁、租户 | [src/CLAUDE.md](src/CLAUDE.md) |

## 开发命令

```bash
# 安装依赖
uv sync

# 启动 Web 服务器
uv run runserver

# 指定主机/端口启动
uv run runserver --host 0.0.0.0 --port 8080

# 开发模式（热重载）
uv run runserver --reload

# 测试
uv run pytest
uv run pytest -v
uv run pytest tests/demo/unit/
```

## 数据库迁移

项目采用模块化迁移架构，支持多业务模块独立迁移和数据初始化。

### 迁移命令

```bash
# 查看迁移状态
uv run python scripts/migrate_db.py --status

# 执行所有待执行的迁移
uv run python scripts/migrate_db.py

# 预览待执行的迁移 SQL（不执行）
uv run python scripts/migrate_db.py --dry-run

# 回滚迁移
uv run python scripts/migrate_db.py --downgrade
```

### 创建新迁移

```bash
# 创建迁移文件（自动检测模型变更）
alembic revision --autogenerate -m "add user tables"

# 创建空迁移文件（手动编写 SQL）
alembic revision -m "custom migration"
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
down_revision = "001_tenant"  # 上一个迁移的 revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建表
    op.create_table("users", ...)


def downgrade() -> None:
    # 删除表
    op.drop_table("users")
```

## 数据初始化

数据初始化脚本位于 `src/demo/seeds/`，支持幂等执行和 dry-run 预览。

### 初始化命令

```bash
# 初始化所有模块的默认数据
uv run python scripts/seed_data.py

# 预览待执行的数据初始化（不写入数据库）
uv run python scripts/seed_data.py --dry-run

# 初始化指定模块
uv run python scripts/seed_data.py --module tenant
uv run python scripts/seed_data.py --module user
```

### 种子脚本规范

每个模块的种子脚本放在 `src/demo/seeds/` 目录：

```text
src/demo/seeds/
├── __init__.py
├── tenant_seed.py      # 租户模块初始数据
├── user_seed.py        # 用户模块初始数据
└── ...
```

种子脚本示例：

```python
# src/demo/seeds/tenant_seed.py
"""租户模块数据初始化"""

import asyncio
from sqlalchemy import select
from demo.models.core.engine import get_engine
from demo.models.tenant import Tenant


async def run(*, dry_run: bool = False) -> int:
    """初始化租户数据

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    engine = get_engine()
    async with engine.begin() as conn:
        # 检查是否已存在
        result = await conn.execute(select(Tenant).limit(1))
        if result.scalar():
            print("  租户数据已存在，跳过初始化")
            return 0

        if dry_run:
            print("  [DRY-RUN] 将创建默认租户: default")
            return 1

        # 创建默认租户
        tenant = Tenant(
            id="default",
            name="默认租户",
            code="default",
        )
        conn.add(tenant)
        await conn.commit()

        print("  已创建默认租户: default")
        return 1
```

### 模块注册

在 `src/demo/seeds/__init__.py` 中注册模块：

```python
from demo.seeds.tenant_seed import run as tenant_run
from demo.seeds.user_seed import run as user_run

SEED_MODULES = {
    "tenant": tenant_run,
    "user": user_run,
}
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
