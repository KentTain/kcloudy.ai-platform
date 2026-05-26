# Python 后端指南

本文件为 Claude Code 在 `server/python/` Python 后端项目中工作时提供指导。

## 项目定位

Python 后端使用 FastAPI + SQLAlchemy 2.0 构建，是 InitProject 的 Python 技术栈实现。项目采用 **模块化单体架构**，支持模块独立部署。

## 架构特性

- **模块级 Schema 隔离**：每个业务模块拥有独立的 PostgreSQL schema
- **模块动态加载**：通过 `module.py` 声明模块信息，支持按需加载
- **模块独立部署**：每个模块可通过 `app.py` 提供独立应用工厂

## 技术栈

| 类别 | 技术 |
| --- | --- |
| Web 框架 | FastAPI |
| ORM / 迁移 | SQLAlchemy 2.0、Alembic |
| 配置 / 校验 | Pydantic 2.x、YAML 配置 |
| AI 示例 | LangChain、LangGraph、MCP 示例 |
| 数据服务 | PostgreSQL（含 pgvector）、Redis、MinIO |
| 测试 | pytest、pytest-asyncio、pytest-mock |
| 代码质量 | Ruff |

## 关键目录

| 路径 | 用途 | 详细文档 |
| --- | --- | --- |
| `src/` | 源码目录，按顶级模块组织 | [src/CLAUDE.md](src/CLAUDE.md) |
| `src/framework/` | 基础设施模块 | [src/framework/CLAUDE.md](src/framework/CLAUDE.md) |
| `src/framework/module/` | 模块系统（动态加载、注册中心） | [src/framework/module/CLAUDE.md](src/framework/module/CLAUDE.md) |
| `src/tenant/` | 租户管理模块 | [src/tenant/CLAUDE.md](src/tenant/CLAUDE.md) |
| `src/iam/` | 身份认证与权限模块 | [src/iam/CLAUDE.md](src/iam/CLAUDE.md) |
| `src/demo/` | AI 助手平台演示模块 | [src/CLAUDE.md](src/CLAUDE.md) |
| `tests/` | 测试目录，按源码模块组织 | [tests/CLAUDE.md](tests/CLAUDE.md) |
| `tests/framework/` | framework 测试 | [tests/framework/CLAUDE.md](tests/framework/CLAUDE.md) |
| `tests/demo/` | demo 测试 | [tests/demo/CLAUDE.md](tests/demo/CLAUDE.md) |
| `config/` | 指向 `server/config/` 的配置目录 | - |
| `manage.py` | 统一管理脚本 | - |
| `pyproject.toml` | 项目与依赖配置 | - |
| `pytest.ini` | pytest 配置 | - |
| `.ruff.toml` | Ruff 配置 | - |

## 模块边界

- 模块是顶级目录 `src/{module}/`，功能是模块内部子域。
- 业务模块包括 `demo`、`tenant`、`iam`，可以依赖 `framework`。
- `framework` 是底层基础设施模块，禁止依赖业务模块。
- 可复用基础能力优先放入 `framework`；业务专属逻辑保留在业务模块内。
- 测试目录与源码模块对齐：`tests/{module}/` 对应 `src/{module}/`。

## 模块结构

每个业务模块包含以下关键文件：

| 文件 | 用途 |
| --- | --- |
| `module.py` | 模块声明，实现 `ModuleDescriptor` 协议 |
| `app.py` | 独立应用工厂，支持单模块部署 |
| `models/__init__.py` | 使用 `create_module_base(schema)` 创建模块 Base |
| `migrations/env.py` | 配置 `version_table_schema` |

## 常用命令

### 启动服务

```bash
# 查看帮助
uv run python manage.py --help

# 启动 Web 服务（加载所有模块）
uv run python manage.py runserver

# 启动 Web 服务（按需加载模块）
uv run python manage.py runserver --module iam,demo

# 开发模式热重载
uv run python manage.py runserver --reload

# 指定主机和端口
uv run python manage.py runserver --host 0.0.0.0 --port 8080

# 启动定时任务调度器（所有模块）
uv run python manage.py runtask

# 启动定时任务调度器（指定模块）
uv run python manage.py runtask --module demo

# 启动消息监听器（指定模块）
uv run python manage.py runlistener --module demo
```

### 数据库迁移

```bash
# 查看所有模块数据库版本
uv run python manage.py db current

# 执行指定模块迁移
uv run python manage.py db migrate --module iam

# 执行所有模块迁移
uv run python manage.py db migrate --all

# 预览迁移 SQL
uv run python manage.py db migrate --sql

# 回滚指定模块迁移
uv run python manage.py db downgrade --module iam

# 查看迁移历史
uv run python manage.py db history --module iam

# 创建迁移
uv run python manage.py db makemigrations --module iam -m "add oauth"

# 重建模块 Schema（危险操作）
uv run python manage.py db rebuild --module iam
uv run python manage.py db rebuild --all
```

所有 `db` 命令支持 `-d/--database-url` 指定连接：

```bash
uv run python manage.py db -d "postgresql+asyncpg://user:pass@host:5432/dbname" migrate --module iam
```

### 数据初始化

```bash
# 初始化所有模块默认数据
uv run python manage.py seed

# dry-run 预览
uv run python manage.py seed --dry-run

# 初始化指定模块
uv run python manage.py seed --module iam
```

### 运行测试

```bash
# 全部测试
uv run pytest

# 指定模块
uv run pytest tests/demo/ -v
uv run pytest tests/framework/ -v

# 跳过慢测试
uv run pytest -m "not slow"
```

## 配置管理

配置文件统一位于 `server/config/`，本目录下的 `config/` 为链接或映射入口。

```bash
cp server/config/application-local.yml.example server/config/application-local.yml
```

环境通过 `PYTHON_SERVICE_ENV` 选择，默认 `local`。配置优先级遵循环境变量覆盖环境配置、环境配置覆盖基础配置。

## 代码质量约定

- Python 版本：3.12+。
- 行宽：88 字符。
- Linter / Formatter：Ruff。
- ORM 字段：使用 SQLAlchemy 2.0 `Mapped[...]` / `mapped_column(...)`。
- 模块模型：使用 `create_module_base(schema)` 创建模块级 Base。
- 异步测试：使用 `pytest.mark.asyncio`。
- 新增或修改模块时同步检查对应测试和模块级文档。

## 环境要求

- Python 3.12+
- uv
- PostgreSQL 14+
- Redis 6+
- MinIO（对象存储相关集成测试或功能需要）

## License

Copyright © 2025 Moles. All Rights Reserved.
