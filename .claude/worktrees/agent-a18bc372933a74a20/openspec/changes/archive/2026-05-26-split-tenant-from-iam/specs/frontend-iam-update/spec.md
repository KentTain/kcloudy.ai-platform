## MODIFIED Requirements

### Requirement: 前端 IAM 模块精简

前端 SHALL 移除 IAM 模块中的租户相关代码。

#### Scenario: API 文件移除

- **WHEN** 查看 `web/vue/src/iam/api/` 目录
- **THEN** 不存在 `tenant.ts` 文件
- **AND** 存在 `auth.ts`、`user.ts`、`role.ts`、`permission.ts`、`department.ts`

#### Scenario: API 索引更新

- **WHEN** 查看 `web/vue/src/iam/api/index.ts`
- **THEN** 不导出 `tenant` 相关 API

#### Scenario: 页面目录移除

- **WHEN** 查看 `web/vue/src/iam/pages/` 目录
- **THEN** 不存在 `tenants/` 目录
- **AND** 存在 `users/`、`roles/`、`permissions/`、`departments/`、`profile/`

#### Scenario: 路由配置更新

- **WHEN** 查看 `web/vue/src/iam/router/index.ts`
- **THEN** 不包含以下路由：
  - `tenants`
  - `tenants/create`
  - `tenants/:id`
  - `tenants/:id/edit`
- **AND** 保留用户、角色、权限、部门、个人中心路由

### Requirement: IAM 模块入口更新

前端 SHALL 更新 IAM 模块入口，移除租户相关导出。

#### Scenario: 入口文件更新

- **WHEN** 查看 `web/vue/src/iam/index.ts`
- **THEN** 不导出租户相关 API 和类型
- **AND** 保留用户、角色、权限、部门相关导出

### Requirement: 框架路由注册更新

前端框架 SHALL 注册新的 Tenant 模块路由。

#### Scenario: 路由注册

- **WHEN** 查看框架路由配置文件
- **THEN** 注册 `tenantRoutes` 到 `/admin` 路由下
- **AND** 租户路由路径 `/admin/tenants` 保持有效
