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
| `migrations/env.py` | 配置 `version_table_schema` |

## 核心命令

```bash
# 启动 Web 服务
uv run python manage.py runserver
uv run python manage.py runserver --module iam,demo

# 数据库迁移
uv run python manage.py db migrate --module iam
uv run python manage.py db migrate --all

# 数据初始化
uv run python manage.py seed

# 运行测试
uv run pytest
uv run pytest tests/demo/ -v
```

## 开发约束

- Python 版本：3.12+
- ORM 字段：使用 SQLAlchemy 2.0 `Mapped[...]` / `mapped_column(...)`
- 模块模型：使用 `create_module_base(schema)` 创建模块级 Base
- 异步测试：使用 `pytest.mark.asyncio`
- API 路由：遵循 `/{模块}/{类型}/v1/{功能}` 格式

## API 路由规范

### 路由格式

**统一格式**：`/{模块}/{类型}/v1/{功能}`

| 模块 | 类型 | 功能示例 | 完整路径 |
|------|------|---------|---------|
| tenant | admin | tenants | `/tenant/admin/v1/tenants` |
| tenant | console | tenants | `/tenant/console/v1/tenants` |
| iam | admin | users | `/iam/admin/v1/users` |
| iam | console | auth/login | `/iam/console/v1/auth/login` |
| ai | admin | models | `/ai/admin/v1/models` |
| ai | console | chat-messages | `/ai/console/v1/chat-messages` |

### 中间件策略

| 路径前缀 | 认证方式 |
|---------|---------|
| `/tenant/admin/*` | AdminAuthMiddleware（租户管理员 Token） |
| `/tenant/console/*` | IAMAuthMiddleware（JWT Token） |
| `/iam/*` | IAMAuthMiddleware（JWT Token） |
| `/ai/*` | IAMAuthMiddleware（JWT Token） |
| `/*/inner/*` | 无认证（模块间内部调用） |

### 接口类型

| 类型 | 用途 | 权限要求 |
|------|------|---------|
| admin | 管理后台接口 | 需要管理员权限 |
| console | 用户端接口 | 需要登录用户权限 |
| inner | 内部接口 | 无认证，仅供模块间调用 |

## 测试

测试文件位于 `tests/` 目录，详见 [tests/CLAUDE.md](tests/CLAUDE.md)。

## 环境要求

- Python 3.12+
- uv
- PostgreSQL 14+
- Redis 6+
- MinIO（对象存储相关功能需要）

详细使用示例、跨 Schema 外键处理、常见问题见 [README.md](README.md)。
