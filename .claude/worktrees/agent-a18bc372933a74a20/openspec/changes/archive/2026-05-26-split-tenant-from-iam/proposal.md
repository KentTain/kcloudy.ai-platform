## Why

当前 IAM 模块职责过重，同时承担身份认证（Identity）和访问控制（Access Management）以及租户管理三重职责。Tenant（租户）作为多租户系统的核心基础设施概念，不应绑定在 IAM 模块中。拆分后可明确职责边界，支持 Tenant 模块独立部署，为多业务系统共享租户能力奠定基础。

## What Changes

### 后端变更

- **新增** `src/tenant/` 模块，包含租户核心功能
  - 租户模型：`Tenant`、`TenantConfig`、`TenantAdmin`
  - 租户服务：`TenantService`、`TenantProviderImpl`
  - 控制器：`admin/`、`console/`、`inner/`（新增内部接口层）
  - 数据库 schema：`tenant`
  - 迁移文件和 seed 数据

- **修改** `src/iam/` 模块，移除租户相关内容
  - 移除模型：`Tenant`、`TenantConfig`、`TenantAdmin`（迁移至 tenant 模块）
  - 保留模型：`UserTenant`（与 User 强关联）
  - 新增控制器：`inner/` 内部接口层

- **新增** `/inner/v1/*` 内部接口层
  - 供模块间调用，不对外暴露
  - 支持单体模式（直接 Service 调用）和微服务模式（HTTP 调用）
  - 租户接口：`GET /inner/v1/tenants/{id}`、`POST /inner/v1/tenants/batch`
  - 用户接口：`GET /inner/v1/users/{id}`、`POST /inner/v1/users/batch`

- **新增** `InnerHttpClient` 和模块 Client 封装
  - 统一模块间调用入口
  - 支持配置切换单体/微服务模式

### 前端变更

- **新增** `web/vue/src/tenant/` 模块
  - 租户 API：`api/tenant.ts`
  - 租户页面：`pages/tenants/`
  - 租户路由：`router/index.ts`

- **修改** `web/vue/src/iam/` 模块
  - 移除租户相关 API、页面、路由

### 数据库变更

- **新增** `tenant` schema，包含 `tenants`、`tenant_configs`、`tenant_admins` 表
- **修改** `iam` schema，`user_tenants` 表保留（跨 schema 引用 tenant.tenants）
- **BREAKING** 迁移顺序变更：tenant 模块必须先于 iam 模块迁移

## Capabilities

### New Capabilities

- `tenant-module`: 独立的租户管理模块，提供租户 CRUD、资源配置、全局管理员管理
- `inner-api`: 内部接口层，供模块间调用，支持单体和微服务模式
- `module-client`: 模块间调用客户端封装，统一调用入口，支持模式切换
- `frontend-tenant`: 前端租户模块，包含租户 API、类型定义、页面组件和路由
- `frontend-iam-update`: 前端 IAM 模块更新，移除租户相关代码

### Modified Capabilities

- `iam-module`: IAM 模块职责变更，移除租户管理功能，保留用户-租户关联，新增内部接口

## Impact

### 受影响的代码

| 模块 | 影响 |
|------|------|
| `server/python/src/iam/` | 移除 tenant 相关代码，新增 inner 控制器 |
| `server/python/src/demo/` | 可能需要更新租户上下文获取方式 |
| `web/vue/src/iam/` | 移除 tenant 相关代码 |
| `web/vue/src/framework/` | 路由注册需要支持新模块 |

### 受影响的 API 端点

| 端点 | 变更 |
|------|------|
| `/admin/v1/tenants/*` | 从 IAM 模块迁移至 Tenant 模块 |
| `/console/v1/tenants/*` | 从 IAM 模块迁移至 Tenant 模块 |
| `/inner/v1/tenants/*` | 新增内部接口 |
| `/inner/v1/users/*` | 新增内部接口 |

### 依赖关系变更

```
拆分前：
  demo → iam（包含 tenant）
  iam → framework

拆分后：
  demo → iam, tenant
  iam → tenant（通过 inner 接口）
  tenant → framework
```

### 迁移策略

1. 创建 `tenant` schema 和表
2. 迁移现有 `tenants`、`tenant_configs`、`tenant_admins` 数据
3. 更新 `iam.user_tenants` 表的 schema 归属
4. 重建所有模块的迁移版本
