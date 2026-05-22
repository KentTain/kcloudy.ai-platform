# IAM 模块开发指南

本文件为 Claude Code 在 `src/iam/` 身份认证与权限模块中工作时提供指导。

## 模块定位

IAM（Identity and Access Management）负责租户、用户、认证、角色、权限、组织架构、OAuth 连接和租户资源配置。它是业务模块，可以依赖 `framework`，但不应把 IAM 专属逻辑下沉到 framework。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `controllers/` | FastAPI 路由控制器，包含后台、控制台和通用接口 |
| `services/` | 认证、租户、用户、部门、角色、权限、OAuth 等业务逻辑 |
| `models/` | IAM 数据库模型与枚举 |
| `schemas/` | 请求、响应、Token、登录、租户等 Pydantic 模型 |
| `migrations/` | IAM 数据库迁移与种子数据 |
| `middlewares/` | IAM 鉴权与租户上下文中间件 |
| `initializers/` | 启动初始化逻辑（如存在） |

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 租户管理 | 租户创建、配置、过期管理、租户管理员初始化 |
| 用户认证 | 登录、密码验证、JWT 令牌、Token Schema |
| 权限控制 | 基于角色的访问控制，管理角色与权限映射 |
| 组织架构 | 部门、用户、用户租户关系管理 |
| OAuth 集成 | 第三方 OAuth 连接与用户同步 |
| 租户上下文 | 解析 `X-Tenant-Id`，注入当前租户上下文 |
| 资源配置 | 租户级数据库、存储、缓存物理隔离配置 |

## 角色体系

| 角色 | 职责 | 场景 |
| --- | --- | --- |
| 租户管理员 | 创建租户、管理租户级系统管理员 | 系统初始化与租户开通 |
| 系统管理员 | 管理本租户组织、用户、角色、权限 | 租户内管理操作 |
| 普通用户 | 使用业务功能与维护个人信息 | 日常登录和业务访问 |

## 开发规则

- Controller 只处理路由、参数校验、鉴权依赖和响应封装；业务逻辑放在 Service。
- Service 负责事务边界、业务校验和跨模型协作；不要在 Controller 中直接拼装复杂查询。
- Model 使用 framework 的数据库基类、Mixin 和 SQLAlchemy 2.0 声明式类型。
- Schema 区分请求 DTO、响应 VO 和内部数据结构，避免把数据库模型直接暴露给 API。
- IAM 需要向 framework 提供租户信息时，通过 `tenant_provider_impl` 等适配器实现 framework Protocol。
- 新增 IAM 表必须添加迁移文件；涉及默认角色、权限、管理员时同步更新 seed。

## 启动初始化

应用启动时会执行 IAM seed，初始化默认租户、预定义角色权限和默认租户管理员。初始化异常应记录日志，但不应阻止应用启动，除非该异常会导致后续认证链路不可用。

## 租户资源配置

Tenant / TenantConfig 相关模型支持以下物理隔离配置：

| 类型 | 关键字段 | 说明 |
| --- | --- | --- |
| 数据库 | `db_type`、`db_host`、`db_port`、`db_name`、`db_username`、`db_password` | 配置 `db_name` 后启用租户独立数据库 |
| 存储 | `storage_type`、`storage_bucket` | 配置 `storage_bucket` 后启用租户独立 Bucket |
| 缓存 | `cache_db` | 配置 Redis DB 编号后启用租户独立 Redis DB |
| 加密 | `encryption_key` | 租户密钥由主密钥加密保存 |

`db_password` 和 `encryption_key` 等敏感字段必须加密保存，主密钥通过 `TENANT_ENCRYPTION_MASTER_KEY` 提供。

## API 入口

| 前缀 | 用途 |
| --- | --- |
| `/admin/v1/tenants` | 管理后台租户 CRUD 与资源配置校验 |
| `/console/v1/tenants` | 用户端租户接口 |
| `/api/v1/auth` | 登录、刷新 Token 等认证接口 |
| `/api/v1/users` | 用户管理 |
| `/api/v1/departments` | 部门管理 |
| `/api/v1/roles` | 角色管理 |
| `/api/v1/permissions` | 权限管理 |
| `/api/v1/oauth` | OAuth 连接与同步 |

以实际路由注册为准，修改接口时同步检查对应 Controller、Schema、Service 和测试。

## 测试

IAM 相关能力当前主要通过 framework 租户集成测试和 IAM 服务 / 控制器测试覆盖。新增认证、权限、租户资源配置逻辑时，应补充以下测试：

- Service 单元测试：业务规则、异常路径、事务行为。
- API 集成测试：鉴权、租户上下文、权限边界。
- Seed / migration 验证：默认角色、权限、管理员与数据库结构一致。

通用测试命令和标记见 [../../tests/CLAUDE.md](../../tests/CLAUDE.md)。
