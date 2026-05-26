# IAM 模块开发指南

本文件为 Claude Code 在 `src/iam/` 身份认证与权限模块中工作时提供指导。

## 模块定位

IAM（Identity and Access Management）负责用户认证、角色、权限、组织架构和 OAuth 连接。它是业务模块，可以依赖 `framework` 和 `tenant` 模块，但不应把 IAM 专属逻辑下沉到 framework。

**依赖关系：**
- IAM → framework（基础设施）
- IAM → tenant（通过 inner 接口获取租户信息）

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `controllers/` | FastAPI 路由控制器，包含 admin、console 和 inner 三层 |
| `services/` | 认证、用户、部门、角色、权限、OAuth 等业务逻辑 |
| `models/` | IAM 数据库模型与枚举 |
| `schemas/` | 请求、响应、Token、登录等 Pydantic 模型 |
| `migrations/` | IAM 数据库迁移与种子数据 |
| `middlewares/` | IAM 鉴权与租户上下文中间件 |

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 用户认证 | 登录、密码验证、JWT 令牌、Token Schema |
| 权限控制 | 基于角色的访问控制，管理角色与权限映射 |
| 组织架构 | 部门、用户、用户租户关系管理 |
| OAuth 集成 | 第三方 OAuth 连接与用户同步 |
| 内部接口 | 供其他模块调用的 `/inner/v1/users/*`、`/inner/v1/departments/*` 接口 |

## 接口分层

| 前缀 | 用途 | 权限 |
| --- | --- | --- |
| `/admin/v1/users` | 管理后台用户管理 | 系统管理员 |
| `/console/v1/users` | 用户端接口（个人中心） | 登录用户 |
| `/inner/v1/users` | 内部接口，供模块间调用 | 无（模块内部调用） |
| `/inner/v1/departments` | 内部接口，部门树查询 | 无（模块内部调用） |

## 角色体系

| 角色 | 职责 | 场景 |
| --- | --- | --- |
| 系统管理员 | 管理本租户组织、用户、角色、权限 | 租户内管理操作 |
| 普通用户 | 使用业务功能与维护个人信息 | 日常登录和业务访问 |

**注意：** 租户管理员（tenant_admin）角色已迁移至 Tenant 模块管理。

## 开发规则

- Controller 只处理路由、参数校验、鉴权依赖和响应封装；业务逻辑放在 Service。
- Service 负责事务边界、业务校验和跨模型协作；不要在 Controller 中直接拼装复杂查询。
- Model 使用 framework 的数据库基类、Mixin 和 SQLAlchemy 2.0 声明式类型。
- Schema 区分请求 DTO、响应 VO 和内部数据结构，避免把数据库模型直接暴露给 API。
- Department 模型继承 `TreeNodeMixin`，树字段（tree_leaf、tree_level、tree_sort 等）由 Mixin 自动维护，Service 不应手动管理树字段。

## 内部接口

IAM 模块提供以下内部接口供其他模块调用：

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/inner/v1/users/{user_id}` | GET | 获取单个用户 |
| `/inner/v1/users/batch` | POST | 批量获取用户 |
| `/inner/v1/users/{user_id}/departments` | GET | 获取用户部门 |
| `/inner/v1/departments/tree` | GET | 获取部门树 |
| `/inner/v1/health` | GET | 健康检查 |

调用方式支持两种模式：
- **单体模式**：直接调用 `UserService`、`DepartmentService` 方法
- **微服务模式**：通过 `IamClient`（`framework/clients/iam_client.py`）HTTP 调用

## 数据库模型

| 模型 | 说明 | Schema |
| --- | --- | --- |
| `User` | 用户实体 | `iam.users` |
| `Role` | 角色 | `iam.roles` |
| `Permission` | 权限 | `iam.permissions` |
| `Department` | 部门 | `iam.departments` |
| `UserRole` | 用户-角色关联 | `iam.user_roles` |
| `RolePermission` | 角色-权限关联 | `iam.role_permissions` |
| `UserTenant` | 用户-租户关联 | `iam.user_tenants` |

**注意：** `Tenant`、`TenantConfig`、`TenantAdmin` 模型已迁移至 Tenant 模块。

## API 入口

| 前缀 | 用途 |
| --- | --- |
| `/api/v1/auth` | 登录、刷新 Token 等认证接口 |
| `/api/v1/users` | 用户管理 |
| `/api/v1/departments` | 部门管理 |
| `/api/v1/roles` | 角色管理 |
| `/api/v1/permissions` | 权限管理 |
| `/api/v1/oauth` | OAuth 连接与同步 |

以实际路由注册为准，修改接口时同步检查对应 Controller、Schema、Service 和测试。

## 模块拆分说明

2026-05，租户管理功能从 IAM 模块拆分至独立的 Tenant 模块：

- **迁移至 Tenant 模块**：`Tenant`、`TenantConfig`、`TenantAdmin` 模型及相关控制器、服务
- **保留在 IAM 模块**：`UserTenant` 模型（用户-租户关联），通过 inner 接口调用 Tenant 模块

详见 [../tenant/CLAUDE.md](../tenant/CLAUDE.md)。

## 测试

IAM 相关能力当前主要通过 framework 租户集成测试和 IAM 服务 / 控制器测试覆盖。新增认证、权限逻辑时，应补充以下测试：

- Service 单元测试：业务规则、异常路径、事务行为。
- API 集成测试：鉴权、租户上下文、权限边界。
- Seed / migration 验证：默认角色、权限与数据库结构一致。

通用测试命令和标记见 [../../tests/CLAUDE.md](../../tests/CLAUDE.md)。
