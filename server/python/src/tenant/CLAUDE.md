# Tenant 模块开发指南

本文件为 Claude Code 在 `src/tenant/` 租户管理模块中工作时提供指导。

## 模块定位

Tenant 模块负责多租户系统的核心租户管理功能，包括租户 CRUD、租户配置、全局管理员管理和内部接口。它是从 IAM 模块拆分出来的独立模块，遵循模块化单体架构。

**依赖关系：**
- Tenant 是基础模块，无依赖其他业务模块
- IAM 模块依赖 Tenant 模块（通过 inner 接口或直接调用）
- Demo 等业务模块可依赖 Tenant 模块

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `controllers/` | FastAPI 路由控制器，包含 admin、console 和 inner 三层 |
| `services/` | 租户业务逻辑、TenantProvider 实现 |
| `models/` | 租户数据库模型（Tenant、TenantConfig、TenantAdmin）与枚举 |
| `schemas/` | 请求、响应 Pydantic 模型，区分 admin 和 console |
| `migrations/` | 租户数据库迁移与 seed 数据 |
| `middlewares/` | 租户管理员鉴权中间件 |

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 租户管理 | 租户创建、更新、删除、激活、停用 |
| 租户配置 | 租户级数据库、存储、缓存物理隔离配置 |
| 全局管理员 | 租户管理员账号管理，不属于任何租户 |
| 内部接口 | 供其他模块调用的 `/inner/v1/tenants/*` 接口 |

## 接口分层

| 前缀 | 用途 | 权限 |
| --- | --- | --- |
| `/admin/v1/tenants` | 管理后台租户 CRUD | 租户管理员 |
| `/console/v1/tenants` | 用户端租户接口（当前租户、切换租户） | 登录用户 |
| `/inner/v1/tenants` | 内部接口，供模块间调用 | 无（模块内部调用） |

## 数据库模型

| 模型 | 说明 | Schema |
| --- | --- | --- |
| `Tenant` | 租户实体 | `tenant.tenants` |
| `TenantConfig` | 租户资源配置（数据库、存储、缓存） | `tenant.tenant_configs` |
| `TenantAdmin` | 全局管理员账号 | `tenant.tenant_admins` |

## 内部接口

Tenant 模块提供以下内部接口供其他模块调用：

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/inner/v1/tenants/{tenant_id}` | GET | 获取单个租户 |
| `/inner/v1/tenants/batch` | POST | 批量获取租户 |
| `/inner/v1/tenants/{tenant_id}/validate` | GET | 验证租户访问权限 |
| `/inner/v1/health` | GET | 健康检查 |

调用方式支持两种模式：
- **单体模式**：直接调用 `TenantService` 方法
- **微服务模式**：通过 `TenantClient`（`framework/clients/tenant_client.py`）HTTP 调用

## 开发规则

- Controller 只处理路由、参数校验和响应封装；业务逻辑放在 Service。
- Service 负责事务边界、业务校验和跨模型协作。
- Model 使用 framework 的数据库基类、Mixin 和 SQLAlchemy 2.0 声明式类型。
- Schema 区分请求 DTO 和响应 VO，避免暴露数据库模型。
- 新增租户相关表必须添加迁移文件；涉及默认租户时同步更新 seed。
- 敏感配置（如数据库密码、加密密钥）必须使用 AES-256-GCM 加密保存。

## 租户资源配置

TenantConfig 支持以下物理隔离配置：

| 类型 | 关键字段 | 说明 |
| --- | --- | --- |
| 数据库 | `db_type`、`db_host`、`db_port`、`db_name`、`db_username`、`db_password` | 配置后启用租户独立数据库 |
| 存储 | `storage_type`、`storage_bucket` | 配置后启用租户独立 Bucket |
| 缓存 | `cache_db` | 配置 Redis DB 编号后启用租户独立 Redis DB |
| 加密 | `encryption_key` | 租户密钥由主密钥加密保存 |

## 迁移说明

Tenant 模块从 IAM 模块拆分而来（2026-05），原 IAM 模块中的以下内容已迁移至本模块：

- `Tenant`、`TenantConfig`、`TenantAdmin` 模型
- `/admin/v1/tenants/*` 控制器
- `/console/v1/tenants/*` 控制器
- `TenantService`、`TenantProviderImpl` 服务

IAM 模块保留了 `UserTenant` 模型（用户-租户关联），并通过 inner 接口调用 Tenant 模块获取租户信息。

## 测试

Tenant 相关测试位于 `tests/tenant/` 目录：

```bash
# 运行 Tenant 模块测试
uv run pytest tests/tenant/ -v
```

通用测试命令和标记见 [../../tests/CLAUDE.md](../../tests/CLAUDE.md)。
