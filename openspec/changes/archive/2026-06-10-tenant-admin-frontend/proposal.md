# 租户管理前端功能

## 为什么

后端 `tenant-module-system` 变更已完成租户管理的完整 API 实现，包括资源配置、模块定义、模块分配等功能。前端需要配套的管理界面，让管理员能够操作这些功能。

本次变更实现租户管理模块的前端页面，参照 Alon 项目的系统管理页面风格，使用已迁移的通用组件（DataTable、MessageBox 等）构建。

## 变更内容

### 新增页面

- **资源配置管理页面** (`/admin/resource-configs`)：Tab 切换管理数据库、存储、缓存、队列、发布订阅配置，支持 CRUD 和连通性测试
- **模块管理页面** (`/admin/modules`)：模块列表和模块详情（含菜单、权限、角色管理）
- **租户详情页扩展**：新增「资源绑定」和「模块分配」Tab

### 新增 API 模块

- `api/resourceConfig.ts`：资源配置 API（5 种类型各 6 个端点）
- `api/module.ts`：模块管理 API
- `api/tenantModule.ts`：租户模块分配 API

### 更新页面

- `TenantDetail.vue`：扩展为 Tab 结构
- `TenantList.vue`：更新组件引用

## 功能 (Capabilities)

### 新增功能

- `resource-config-management`: 资源配置管理功能，包含数据库、存储、缓存、队列、发布订阅五种资源的 CRUD 和连通性测试
- `module-management`: 模块管理功能，包含模块、模块菜单、模块权限、模块角色的 CRUD
- `tenant-resource-binding`: 租户资源绑定功能，为租户绑定/解绑资源配置
- `tenant-module-assignment`: 租户模块分配功能，为租户分配/取消模块

### 修改功能

- `tenant-management`: 扩展租户详情页，新增资源绑定和模块分配 Tab

## 影响

### 前端代码

- `web/vue/src/tenant/`：新增页面、API、类型定义
- `web/vue/src/components/common/`：复用 DataTable、MessageBox 等组件

### API 端点

- `GET/POST/PUT/DELETE /admin/v1/resource-configs/{type}`：资源配置 CRUD
- `POST /admin/v1/resource-configs/{type}/{id}/test-connection`：连通性测试
- `GET/POST/PUT/DELETE /admin/v1/modules`：模块 CRUD
- `GET/POST/PUT/DELETE /admin/v1/modules/{id}/menus`：模块菜单 CRUD
- `GET/POST/PUT/DELETE /admin/v1/modules/{id}/permissions`：模块权限 CRUD
- `GET/POST/PUT/DELETE /admin/v1/modules/{id}/roles`：模块角色 CRUD
- `GET/POST/DELETE /admin/v1/tenants/{id}/modules`：租户模块分配

### 路由

- 新增 `/admin/resource-configs` 路由
- 新增 `/admin/modules` 及其子路由
- 扩展 `/admin/tenants/:id` 路由结构
