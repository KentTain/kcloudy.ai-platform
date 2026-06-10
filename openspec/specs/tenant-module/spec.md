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

### Requirement: 管理员可以管理模块

系统 SHALL 允许管理员对模块进行创建、查询、更新、删除操作。

#### Scenario: 查询模块列表
- **WHEN** 管理员请求 GET /admin/v1/modules
- **THEN** 系统返回模块列表（分页）

#### Scenario: 创建模块
- **WHEN** 管理员请求 POST /admin/v1/modules 并提供模块信息
- **THEN** 系统创建模块并返回模块信息

#### Scenario: 创建重复编码模块
- **WHEN** 管理员尝试创建已存在编码的模块
- **THEN** 系统返回错误 "模块编码已存在"

#### Scenario: 更新模块
- **WHEN** 管理员请求 PUT /admin/v1/modules/{id} 并提供更新数据
- **THEN** 系统更新模块并返回更新后的数据

#### Scenario: 删除模块
- **WHEN** 管理员请求 DELETE /admin/v1/modules/{id}
- **THEN** 系统删除模块

#### Scenario: 删除已分配模块
- **WHEN** 管理员尝试删除已被租户分配的模块
- **THEN** 系统返回错误 "模块已被租户分配，无法删除"

### Requirement: 管理员可以管理模块菜单

系统 SHALL 允许管理员对模块菜单进行创建、查询、更新、删除操作，菜单为树形结构。

#### Scenario: 查询模块菜单树
- **WHEN** 管理员请求 GET /admin/v1/modules/{id}/menus
- **THEN** 系统返回模块的菜单树形结构

#### Scenario: 创建模块菜单
- **WHEN** 管理员请求 POST /admin/v1/modules/{id}/menus 并提供菜单信息
- **THEN** 系统创建菜单并返回菜单信息

#### Scenario: 创建子菜单
- **WHEN** 管理员创建菜单时指定 parent_id
- **THEN** 系统创建子菜单，关联到父菜单

#### Scenario: 删除有子菜单的菜单
- **WHEN** 管理员尝试删除有子菜单的菜单
- **THEN** 系统返回错误 "菜单有子菜单，无法删除"

#### Scenario: 菜单编辑弹窗
- **WHEN** 管理员点击「新增菜单」或「编辑」按钮
- **THEN** 系统弹出菜单表单弹窗，包含名称、编码、路径、父菜单、图标、排序字段

### Requirement: 管理员可以管理模块权限

系统 SHALL 允许管理员对模块权限进行创建、查询、更新、删除操作。

#### Scenario: 查询模块权限列表
- **WHEN** 管理员请求 GET /admin/v1/modules/{id}/permissions
- **THEN** 系统返回模块的权限列表

#### Scenario: 创建模块权限
- **WHEN** 管理员请求 POST /admin/v1/modules/{id}/permissions 并提供权限信息
- **THEN** 系统创建权限并返回权限信息

#### Scenario: 权限编码格式验证
- **WHEN** 管理员创建权限时编码格式不符合 module:resource:action
- **THEN** 系统返回验证错误

#### Scenario: 操作类型验证
- **WHEN** 管理员创建权限时 action 不是 read/write/delete
- **THEN** 系统返回错误 "操作类型必须是 read/write/delete"

### Requirement: 管理员可以管理模块角色

系统 SHALL 允许管理员对模块角色进行创建、查询、更新、删除操作，并支持为角色分配权限。

#### Scenario: 查询模块角色列表
- **WHEN** 管理员请求 GET /admin/v1/modules/{id}/roles
- **THEN** 系统返回模块的角色列表（包含权限信息）

#### Scenario: 创建模块角色
- **WHEN** 管理员请求 POST /admin/v1/modules/{id}/roles 并提供角色信息
- **THEN** 系统创建角色并返回角色信息

#### Scenario: 更新角色权限
- **WHEN** 管理员请求 PUT /admin/v1/modules/{id}/roles/{roleId}/permissions 并提供权限 ID 列表
- **THEN** 系统更新角色权限（整体替换）

#### Scenario: 修改系统内置角色
- **WHEN** 管理员尝试修改 is_system=true 的角色
- **THEN** 系统返回错误 "系统内置角色禁止修改"

#### Scenario: 删除系统内置角色
- **WHEN** 管理员尝试删除 is_system=true 的角色
- **THEN** 系统返回错误 "系统内置角色禁止删除"

### Requirement: 模块详情页面提供 Tab 切换

系统 SHALL 提供模块详情页，包含基本信息、菜单管理、权限管理、角色管理四个 Tab。

#### Scenario: 查看模块详情
- **WHEN** 管理员访问 /admin/modules/{id}
- **THEN** 系统显示模块详情页，默认展示基本信息 Tab

#### Scenario: 切换 Tab
- **WHEN** 管理员点击不同 Tab
- **THEN** 页面切换显示对应的管理界面

### Requirement: 模块列表页面显示统计卡片

系统 SHALL 在模块列表页面顶部显示统计卡片。

#### Scenario: 显示统计信息
- **WHEN** 管理员进入模块列表页面
- **THEN** 页面顶部显示模块总数、启用模块数、必须模块数、已分配次数
