# Tenant 模块规范

## Purpose

提供独立的租户管理模块，包含租户核心功能，与 IAM 模块解耦，支持独立部署。

## Requirements

### Requirement: 租户模块独立存在

系统 SHALL 提供独立的 `tenant` 模块，包含租户管理的所有功能，与 IAM 模块解耦。

#### Scenario: 模块目录结构

- **WHEN** 查看 `server/python/src/` 目录
- **THEN** 存在 `tenant/` 模块目录
- **AND** 目录包含 `models/`、`services/`、`controllers/`、`migrations/`、`module.py`

#### Scenario: 模块声明文件

- **WHEN** 查看 `tenant/module.py`
- **THEN** 存在 `TenantModule` 类
- **AND** `name` 属性返回 `"tenant"`
- **AND** `schema` 属性返回 `"tenant"`
- **AND** `dependencies` 返回空列表

### Requirement: 租户数据模型迁移

系统 SHALL 将租户相关数据模型从 IAM 模块迁移到 Tenant 模块。

#### Scenario: Tenant 模型迁移

- **WHEN** 查看 `tenant/models/tenant.py`
- **THEN** 存在 `Tenant` 模型类
- **AND** 模型使用 `tenant` schema

#### Scenario: TenantConfig 模型迁移

- **WHEN** 查看 `tenant/models/tenant_config.py`
- **THEN** 存在 `TenantConfig` 模型类
- **AND** 与 `Tenant` 模型为一对一关系

#### Scenario: TenantAdmin 模型迁移

- **WHEN** 查看 `tenant/models/tenant_admin.py`
- **THEN** 存在 `TenantAdmin` 模型类
- **AND** 用于存储全局管理员信息

### Requirement: 租户服务迁移

系统 SHALL 将租户相关服务从 IAM 模块迁移到 Tenant 模块。

#### Scenario: TenantService 迁移

- **WHEN** 查看 `tenant/services/tenant_service.py`
- **THEN** 存在 `TenantService` 类
- **AND** 提供租户 CRUD 操作

#### Scenario: TenantProvider 实现

- **WHEN** 查看 `tenant/services/tenant_provider_impl.py`
- **THEN** 存在 `TenantProviderImpl` 类
- **AND** 实现 `framework.tenant.protocols.TenantProvider` 协议

### Requirement: 租户控制器迁移

系统 SHALL 将租户相关控制器从 IAM 模块迁移到 Tenant 模块。

#### Scenario: Admin 控制器迁移

- **WHEN** 请求 `POST /admin/v1/tenants`
- **THEN** 请求由 `tenant/controllers/admin/tenant_controller.py` 处理
- **AND** 返回正确的租户创建结果

#### Scenario: Console 控制器迁移

- **WHEN** 请求 `GET /console/v1/tenants/current`
- **THEN** 请求由 `tenant/controllers/console/tenant_controller.py` 处理
- **AND** 返回当前租户信息

### Requirement: 租户数据库 Schema

系统 SHALL 创建独立的 `tenant` PostgreSQL schema。

#### Scenario: Schema 创建

- **WHEN** 执行 tenant 模块迁移
- **THEN** 创建 `tenant` schema
- **AND** 创建 `tenants`、`tenant_configs`、`tenant_admins` 表
- **AND** 创建 `tenant.alembic_version` 版本表

#### Scenario: 数据隔离

- **WHEN** 查询租户数据
- **THEN** 数据存储在 `tenant.tenants` 表
- **AND** 与 `iam.users` 表物理隔离

### Requirement: 租户 Seed 数据

系统 SHALL 在 Tenant 模块提供独立的 seed 数据初始化。

#### Scenario: 默认租户创建

- **WHEN** 执行 `python manage.py seed --module tenant`
- **THEN** 创建默认租户
- **AND** 创建默认租户配置
