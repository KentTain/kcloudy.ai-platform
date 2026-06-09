## 为什么

当前租户系统缺乏模块化管理能力：租户无法灵活分配功能模块，模块定义与租户实例耦合，资源配置分散。设计文档已完整规划租户模块化架构，需落地实现以支持多租户 SaaS 场景。

## 变更内容

**新增功能：**
- 租户资源配置管理（Database/Storage/Cache/Queue/PubSub 五类资源的 CRUD 及连通性测试）
- 模块定义层模型（Module、ModuleMenu、ModulePermission、ModuleRole、ModuleRolePermission）
- 租户模块分配（TenantModule 关联，自动同步菜单/权限/角色到租户实例层）
- 领域事件驱动同步（Tenant 模块发布事件，IAM 模块监听处理）

**修改功能：**
- Tenant 模型新增五个资源配置 FK 字段（db_config_id 等）
- 新增 TenantConfig 业务配置模型（max_users 等限额）
- 租户实例层模型（Menu/Permission/Role）新增 ref_id 关联模块定义层

## 功能 (Capabilities)

### 新增功能

- `module-definition`: 模块定义层管理 —— Module、ModuleMenu、ModulePermission、ModuleRole 的 CRUD，支持树形菜单、默认角色定义
- `resource-config`: 资源配置管理 —— Database/Storage/Cache/Queue/PubSub 五类资源的 CRUD 及连通性测试
- `tenant-resource-binding`: 租户资源绑定 —— 租户与资源配置的关联管理
- `tenant-module-assignment`: 租户模块分配 —— TenantModule 分配/取消，自动同步机制
- `module-sync-events`: 模块同步事件 —— ModuleAssigned/ModuleUnassigned 等领域事件定义与发布
- `iam-sync-handlers`: IAM 同步处理器 —— 监听模块事件，自动同步菜单/权限/角色到租户实例层

### 修改功能

- `tenant`: 新增 db_config_id、storage_config_id、cache_config_id、queue_config_id、pubsub_config_id FK 字段；新增 TenantConfig 一对一配置模型
- `iam-rbac`: Menu/Permission/Role 模型新增 ref_id 字段关联模块定义层；UserRole/RolePermission 新增 tenant_id 字段

## 影响

**数据库迁移：**
- 新增 11 张表（TenantConfig、5 张资源配置表、Module 相关 5 张表、TenantModule）
- 修改 Tenant 表（新增 5 个 FK 字段）
- 修改 IAM 模块 6 张表（Menu/Permission/Role 新增 ref_id，UserRole/RolePermission 新增 tenant_id）

**API 端点：**
- `/api/v1/tenant/resource-configs/*` — 资源配置管理（5 类资源各 6 个端点）
- `/api/v1/tenant/tenants/{id}/resources` — 租户资源绑定
- `/api/v1/tenant/modules/*` — 模块定义管理
- `/api/v1/tenant/tenants/{id}/modules` — 租户模块分配

**模块依赖：**
- Tenant 模块发布事件，IAM 模块监听处理（跨模块事件通信）
