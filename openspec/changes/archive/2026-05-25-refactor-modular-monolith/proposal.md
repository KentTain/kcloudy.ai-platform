# Proposal: 模块化单体架构重构

## Why

当前后端架构存在三个核心问题：

1. **数据库隔离不足**：所有模块的表都在 `public` schema，共享同一个 `alembic_version` 版本表，模块无法独立迁移或独立版本控制。
2. **模块加载硬编码**：`application_web.py`、`application_task.py`、`application_listener.py` 通过显式 `import` 装配模块，新增模块必须手动修改这些入口文件。
3. **独立部署受阻**：模块间耦合紧密，无法按需单独部署 IAM 或 Demo 模块。

这些问题限制了系统的可扩展性和运维灵活性。现在是重构的合适时机：模块边界已清晰（`iam`、`demo`、`framework`），业务复杂度尚可控制。

## What Changes

### 数据库层

- **BREAKING** 每个 `schema` 独立管理迁移版本
- 所有模块内的表自动归属对应 schema（通过模块级 `Base` 实现）
- 移除跨模块外键约束，改用应用层一致性检查

### 模块层

- 新增 `src/{module}/module.py`：模块声明文件，用于动态装配
- 新增 `src/{module}/app.py`：独立应用工厂，用于单模块部署
- 每个模块维护自己的 `migrations/env.py`，配置 `version_table_schema`
- Seed 数据回归各自模块管理

### 框架层

- 新增 `framework/database/core/module_base.py`：`create_module_base(schema)` 工厂函数
- 新增 `framework/module/`：`ModuleDescriptor` 协议、模块扫描与注册中心

### 启动层

- **BREAKING** `manage.py` 重构：
  - `runserver`：默认动态装配所有模块，支持 `--module iam,demo` 按需加载
  - `db makemigrations/migrate/downgrade`：按 `--module` 参数路由，支持 `--all`
  - `seed`：按模块执行，支持 `--all`
  - 新增 `db rebuild`：删除 schema 并重建迁移
- `application_*.py` 重写：从硬编码 import 改为动态扫描 `ModuleDescriptor`

## Capabilities

### New Capabilities

- `module-schema-isolation`：模块级 PostgreSQL schema 隔离，每个模块有独立的表空间和迁移版本表
- `module-dynamic-loading`：模块动态发现与装配，通过 `module.py` 声明注册信息
- `module-standalone-deployment`：模块独立部署能力，通过 `app.py` 提供完整应用工厂

### Modified Capabilities

无。此次重构为架构层面变更，不影响现有功能需求规格。

## Impact

### 受影响代码

| 组件 | 改动程度 |
|------|----------|
| `framework/database/core/` | 新增 `module_base.py` |
| `framework/module/` | 新增目录 |
| `iam/models/__init__.py` | 重写 |
| `iam/models/*.py` | 小改（import 路径） |
| `iam/migrations/env.py` | 重写 |
| `iam/module.py` | 新增 |
| `iam/app.py` | 新增 |
| `demo/models/__init__.py` | 重写 |
| `demo/models/dataset.py` | 小改（import 路径） |
| `demo/migrations/env.py` | 重写 |
| `demo/module.py` | 新增 |
| `demo/app.py` | 新增 |
| `application_web.py` | 重写 |
| `application_task.py` | 重写 |
| `application_listener.py` | 重写 |
| `manage.py` | 重写 |
| `alembic.ini` | 重写或废弃 |
| `demo/migrations/seeds/__init__.py` | 重写（seeds 回归各自模块） |
| 测试文件 | 中改（import 路径变化） |

### 数据库迁移策略

需要重建数据库：

1. 删除所有模块 schema（`DROP SCHEMA IF EXISTS iam CASCADE`）
2. 为每个模块创建 schema（`CREATE SCHEMA iam`）
3. 为每个模块运行 `alembic upgrade head`
4. 为每个模块运行 seed 初始化

### API 端点

无变化。路由注册逻辑迁移至 `ModuleDescriptor.get_routers()`，最终路径保持一致。

### 依赖关系

- 无新增外部依赖
- 内部依赖：`framework/module/` 新增对 `fastapi` 的依赖（`ModuleDescriptor` 协议定义）
