# Tenant 模块开发指南

本文件为 Claude Code 在 `web/vue/src/tenant/` 租户管理模块中工作时提供指导。

## 模块定位

Tenant 模块负责前端租户管理功能，包括租户列表、创建、编辑、详情和租户切换。与后端 `server/python/src/tenant/` 模块对齐。

## 目录职责

| 目录 | 职责 |
|------|------|
| api/ | 租户 API 函数 |
| pages/ | 页面组件（TenantList、TenantForm、TenantDetail） |
| router/ | 模块路由配置 |
| stores/ | 租户状态管理 |
| types/ | TypeScript 类型定义 |

## 核心能力

| 能力 | 说明 |
|------|------|
| 租户列表 | 分页查询、搜索、筛选 |
| 租户创建 | 表单验证、提交 |
| 租户编辑 | 修改租户信息 |
| 租户切换 | 用户端切换当前租户 |

## 路由配置

| 路径 | 组件 | 权限 |
|------|------|------|
| /tenants | TenantList | tenant_admin |
| /tenants/create | TenantForm | tenant_admin |
| /tenants/:id | TenantDetail | tenant_admin |
| /tenants/:id/edit | TenantForm | tenant_admin |

## API 函数

| 函数 | 说明 |
|------|------|
| getTenants | 获取租户列表（管理员） |
| createTenant | 创建租户 |
| updateTenant | 更新租户 |
| deleteTenant | 删除租户 |
| getCurrentTenant | 获取当前租户 |
| switchTenant | 切换租户 |

## 开发规则

- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore`
- 页面使用 `AppPage` 组件作为骨架
- 权限检查使用 `frameworkUserStore.hasRole('tenant_admin')`

## 测试

```bash
pnpm test:unit tests/tenant/ --run
```
