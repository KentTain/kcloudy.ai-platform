# Tenant 模块开发指南

本文件为 Claude Code 在 `src/tenant/` 租户管理模块中工作时提供指导。

## 模块定位

Tenant 模块负责多租户系统的核心租户管理功能，包括租户 CRUD、租户配置、全局管理员管理。它是基础模块，无依赖其他业务模块。

## 依赖边界

```
IAM / Demo ──▶ Tenant
Tenant ──X──▶ IAM / Demo
```

- IAM 和 Demo 模块可依赖 Tenant
- Tenant 不依赖其他业务模块

## 目录职责

| 目录 | 职责 |
|------|------|
| controllers/ | FastAPI 路由控制器（admin/console/inner 三层） |
| services/ | 租户业务逻辑、TenantProvider 实现 |
| models/ | 租户数据库模型（Tenant、TenantConfig、TenantAdmin） |
| schemas/ | 请求、响应 Pydantic 模型 |
| migrations/ | 租户数据库迁移与 seed 数据 |

## 接口分层

Tenant 模块 API 路由遵循 `/{模块}/{类型}/v1/{功能}` 格式：

| 类型 | 路由前缀 | 用途 | 权限 |
|------|---------|------|------|
| admin | `/tenant/admin/v1/tenants` | 管理后台租户 CRUD | 租户管理员 Token |
| console | `/tenant/console/v1/tenants` | 用户端租户接口 | JWT Token |
| inner | `/tenant/inner/v1/tenants` | 内部接口，供模块间调用 | 无认证 |

### 完整路由表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tenant/admin/v1/tenants` | 获取租户列表 |
| POST | `/tenant/admin/v1/tenants` | 创建租户 |
| GET | `/tenant/admin/v1/tenants/{id}` | 获取租户详情 |
| PUT | `/tenant/admin/v1/tenants/{id}` | 更新租户 |
| DELETE | `/tenant/admin/v1/tenants/{id}` | 删除租户 |
| GET | `/tenant/console/v1/tenants/current` | 获取当前租户信息 |
| GET | `/tenant/inner/v1/tenants/{id}` | 内部接口：获取租户信息 |

## 数据库模型

| 模型 | 说明 | Schema |
|------|------|--------|
| Tenant | 租户实体 | tenant.tenants |
| TenantConfig | 租户资源配置 | tenant.tenant_configs |
| TenantAdmin | 全局管理员账号 | tenant.tenant_admins |

## 开发规则

- Controller 只处理路由、参数校验和响应封装
- Service 负责事务边界、业务校验和跨模型协作
- 敏感配置（数据库密码、加密密钥）使用 AES-256-GCM 加密保存

## 测试

```bash
uv run pytest tests/tenant/ -v
```
