# Tenant 模块开发指南

本文件为 Claude Code 在 `web/vue/src/tenant/` 租户管理模块中工作时提供指导。

## 模块定位

Tenant 模块负责前端租户管理功能，包括租户列表、创建、编辑、详情和租户切换。它是从 IAM 模块拆分出来的独立模块，与后端 `server/python/src/tenant/` 模块对齐。

## 目录结构

```
tenant/
├── api/
│   ├── tenant.ts       # 租户 API 函数
│   └── index.ts        # API 聚合导出
├── types/
│   └── index.ts        # 类型定义
├── pages/
│   └── tenants/
│       ├── TenantList.vue    # 租户列表页
│       ├── TenantForm.vue    # 租户创建/编辑表单
│       └── TenantDetail.vue  # 租户详情页
├── stores/
│   ├── tenant.ts       # 租户状态管理
│   └── index.ts        # Store 聚合导出
├── router/
│   └── index.ts        # 路由配置
└── index.ts            # 模块入口
```

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 租户列表 | 分页查询、搜索、筛选 |
| 租户创建 | 表单验证、提交 |
| 租户编辑 | 修改租户信息 |
| 租户详情 | 查看租户详细信息 |
| 租户操作 | 激活、停用、删除 |
| 租户切换 | 用户端切换当前租户 |

## API 函数

| 函数 | 方法 | 说明 |
| --- | --- | --- |
| `getTenants` | GET | 获取租户列表（管理员） |
| `getTenant` | GET | 获取租户详情 |
| `createTenant` | POST | 创建租户 |
| `updateTenant` | PUT | 更新租户 |
| `deleteTenant` | DELETE | 删除租户 |
| `activateTenant` | POST | 激活租户 |
| `deactivateTenant` | POST | 停用租户 |
| `getTenantStats` | GET | 获取租户统计 |
| `getCurrentTenant` | GET | 获取当前租户（控制台） |
| `getMyTenants` | GET | 获取用户可切换租户列表 |
| `switchTenant` | POST | 切换租户 |

## 类型定义

| 类型 | 说明 |
| --- | --- |
| `Tenant` | 租户实体 |
| `TenantStatsVo` | 租户统计 |
| `UserTenantVo` | 用户租户信息 |
| `SwitchTenantVo` | 切换租户响应 |
| `TenantQueryParams` | 查询参数 |
| `CreateTenantParams` | 创建参数 |
| `UpdateTenantParams` | 更新参数 |

## 路由配置

| 路径 | 组件 | 权限 |
| --- | --- | --- |
| `/tenants` | TenantList | tenant_admin |
| `/tenants/create` | TenantForm | tenant_admin |
| `/tenants/:id` | TenantDetail | tenant_admin |
| `/tenants/:id/edit` | TenantForm | tenant_admin |

## Store 状态

```typescript
const tenantStore = useTenantStore()

// 状态
tenantStore.tenants        // 租户列表
tenantStore.currentTenant  // 当前租户
tenantStore.myTenants      // 用户可切换租户列表
tenantStore.loading        // 加载状态
tenantStore.total          // 总数

// 方法
tenantStore.fetchTenants()       // 获取租户列表
tenantStore.fetchTenant()        // 获取租户详情
tenantStore.addTenant()          // 创建租户
tenantStore.editTenant()         // 更新租户
tenantStore.removeTenant()       // 删除租户
tenantStore.activate()           // 激活租户
tenantStore.deactivate()         // 停用租户
tenantStore.fetchCurrentTenant() // 获取当前租户
tenantStore.fetchMyTenants()     // 获取可切换租户列表
tenantStore.switchTenant()       // 切换租户
```

## 开发规则

- API 函数使用 `@/framework/api/client` 的 `rawGet`、`rawPost`、`rawPut`、`rawDel` 方法。
- Store 使用 Pinia 的 `defineStore` 和 Composition API。
- 页面组件使用 `AppPage` 组件作为页面骨架。
- 表单验证使用 `vee-validate` + `zod`。
- 权限检查使用 `frameworkUserStore.hasRole('tenant_admin')`。

## 模块拆分说明

2026-05，租户管理功能从 IAM 模块拆分至独立的 Tenant 模块：

- **迁移至 Tenant 模块**：租户 API、类型、页面、路由、Store
- **保留在 IAM 模块**：用户、角色、权限、部门相关功能

个人中心（Profile）页面仍需要租户切换功能，通过导入 `@/tenant/stores/tenant` 使用。

## 与后端对齐

前端 Tenant 模块与后端 `server/python/src/tenant/` 模块对齐：

| 前端路径 | 后端路径 |
| --- | --- |
| `web/vue/src/tenant/` | `server/python/src/tenant/` |
| `api/tenant.ts` | `controllers/admin/tenant_controller.py` |
| `types/index.ts` | `schemas/admin/tenant.py` |
| `router/index.ts` | `module.py` 路由注册 |

API 端点对应：

| 前端 API | 后端端点 |
| --- | --- |
| `getTenants` | `GET /admin/v1/tenants` |
| `createTenant` | `POST /admin/v1/tenants` |
| `getCurrentTenant` | `GET /console/v1/tenants/current` |
| `switchTenant` | `POST /console/v1/tenants/{id}/switch` |
