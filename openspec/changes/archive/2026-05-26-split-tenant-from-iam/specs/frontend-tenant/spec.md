## ADDED Requirements

### Requirement: 前端租户模块独立存在

前端 SHALL 提供独立的 `tenant` 模块，包含租户管理的所有功能，与 IAM 模块解耦。

#### Scenario: 模块目录结构

- **WHEN** 查看 `web/vue/src/` 目录
- **THEN** 存在 `tenant/` 模块目录
- **AND** 目录包含 `api/`、`types/`、`pages/`、`router/`、`index.ts`

#### Scenario: 模块入口文件

- **WHEN** 查看 `web/vue/src/tenant/index.ts`
- **THEN** 导出租户 API、类型定义、路由配置

### Requirement: 租户 API 迁移

前端 SHALL 将租户相关 API 从 IAM 模块迁移到 Tenant 模块。

#### Scenario: API 文件迁移

- **WHEN** 查看 `web/vue/src/tenant/api/tenant.ts`
- **THEN** 存在以下 API 函数：
  - `getTenants` - 获取租户列表
  - `getTenant` - 获取租户详情
  - `createTenant` - 创建租户
  - `updateTenant` - 更新租户
  - `deleteTenant` - 删除租户
  - `activateTenant` - 激活租户
  - `deactivateTenant` - 停用租户
  - `getTenantStats` - 获取租户统计
  - `getCurrentTenant` - 获取当前租户
  - `getMyTenants` - 获取用户可切换租户列表
  - `switchTenant` - 切换租户

#### Scenario: API 类型参数

- **WHEN** 查看 `web/vue/src/tenant/api/tenant.ts`
- **THEN** 定义以下类型：
  - `TenantQueryParams` - 查询参数
  - `CreateTenantParams` - 创建参数
  - `UpdateTenantParams` - 更新参数

### Requirement: 租户类型定义

前端 SHALL 在 Tenant 模块定义租户相关类型。

#### Scenario: 类型文件

- **WHEN** 查看 `web/vue/src/tenant/types/index.ts`
- **THEN** 导出以下类型：
  - `Tenant` - 租户实体
  - `TenantStatsVo` - 租户统计
  - `UserTenantVo` - 用户租户关联
  - `SwitchTenantVo` - 切换租户结果

### Requirement: 租户页面迁移

前端 SHALL 将租户相关页面从 IAM 模块迁移到 Tenant 模块。

#### Scenario: 页面目录结构

- **WHEN** 查看 `web/vue/src/tenant/pages/tenants/` 目录
- **THEN** 存在以下组件：
  - `TenantList.vue` - 租户列表页
  - `TenantForm.vue` - 租户创建/编辑表单
  - `TenantDetail.vue` - 租户详情页

#### Scenario: 页面功能保持

- **WHEN** 访问租户管理页面
- **THEN** 页面功能与迁移前一致
- **AND** 路由路径保持不变 (`/admin/tenants`)

### Requirement: 租户路由配置

前端 SHALL 在 Tenant 模块定义租户相关路由。

#### Scenario: 路由文件

- **WHEN** 查看 `web/vue/src/tenant/router/index.ts`
- **THEN** 导出 `tenantRoutes` 数组
- **AND** 包含以下路由：
  - `tenants` - 租户列表
  - `tenants/create` - 创建租户
  - `tenants/:id` - 租户详情
  - `tenants/:id/edit` - 编辑租户

#### Scenario: 路由元信息

- **WHEN** 查看租户路由配置
- **THEN** 列表路由包含 `meta: { title: "租户管理", icon: "tenant", requiresAuth: true, roles: ["tenant_admin"] }`
- **AND** 详情/编辑路由包含 `meta: { hidden: true }`

### Requirement: 模块导出

前端 SHALL 在 Tenant 模块入口统一导出所有内容。

#### Scenario: 入口文件导出

- **WHEN** 查看 `web/vue/src/tenant/index.ts`
- **THEN** 导出以下内容：
  - `export * from "./api/tenant"`
  - `export * from "./types"`
  - `export { tenantRoutes } from "./router"`
