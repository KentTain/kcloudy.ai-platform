# IAM 模块开发指南

本文件为 Claude Code 在 `src/iam/` 身份认证与权限模块中工作时提供指导。

## 模块定位

IAM（Identity and Access Management）负责用户认证、角色、权限、组织架构和 OAuth 连接。它是业务模块，可以依赖 framework 和 tenant 模块。

## 依赖边界

```
IAM ──▶ framework（基础设施）
IAM ──▶ tenant（通过 inner 接口获取租户信息）
```

## 目录职责

| 目录 | 职责 |
|------|------|
| controllers/ | FastAPI 路由控制器（admin/console/inner 三层） |
| services/ | 认证、用户、组织、角色、权限、OAuth 业务逻辑 |
| models/ | IAM 数据库模型与枚举 |
| schemas/ | 请求、响应、Token、登录等 Pydantic 模型 |
| migrations/ | IAM 数据库迁移与种子数据 |

## 接口分层

IAM 模块 API 路由遵循 `/{模块}/{类型}/v1/{功能}` 格式：

| 类型 | 路由前缀 | 用途 | 权限 |
|------|---------|------|------|
| admin | `/iam/admin/v1/users` | 管理后台用户管理 | JWT Token + 管理员权限 |
| console | `/iam/console/v1/users` | 用户端接口（个人中心） | JWT Token |
| inner | `/iam/inner/v1/users` | 内部接口，供模块间调用 | 无认证 |

### 完整路由表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/iam/console/v1/auth/login` | 用户登录 |
| POST | `/iam/console/v1/auth/logout` | 用户登出 |
| POST | `/iam/console/v1/auth/refresh` | 刷新 Token |
| GET | `/iam/console/v1/users/me` | 获取当前用户信息 |
| GET | `/iam/admin/v1/users` | 获取用户列表 |
| POST | `/iam/admin/v1/users` | 创建用户 |
| GET | `/iam/admin/v1/users/{id}` | 获取用户详情 |
| PUT | `/iam/admin/v1/users/{id}` | 更新用户 |
| DELETE | `/iam/admin/v1/users/{id}` | 删除用户 |
| GET | `/iam/inner/v1/users/{id}` | 内部接口：获取用户信息 |

## 核心能力

| 能力 | 说明 |
|------|------|
| 用户认证 | 登录、密码验证、JWT 令牌 |
| 权限控制 | 基于角色的访问控制 |
| 组织架构 | 组织、用户、用户租户关系管理 |
| OAuth 集成 | 第三方 OAuth 连接与用户同步 |

## 数据库模型

| 模型 | 说明 | Schema |
|------|------|--------|
| User | 用户实体 | iam.users |
| Role | 角色 | iam.roles |
| Permission | 权限 | iam.permissions |
| Organization | 组织 | iam.organizations |
| UserRole | 用户-角色关联 | iam.user_roles |
| UserTenant | 用户-租户关联 | iam.user_tenants |
| RolePermission | 角色-权限关联 | iam.role_permissions |
| MenuPermission | 菜单-权限关联 | iam.menu_permissions |

## 角色编码规范

| 类型 | 编码格式 | 示例 |
|------|----------|------|
| 全局角色 | `{role_name}` | `admin`, `user` |
| 租户角色 | `{tenant_id}:{role_name}` | `tenant-001:owner`, `tenant-001:admin` |

### 租户角色自动创建

创建租户时自动创建三个租户级角色：

| 角色 | 编码 | 权限 |
|------|------|------|
| 租户所有者 | `{tenant_id}:owner` | 所有模块的所有权限 |
| 租户管理员 | `{tenant_id}:admin` | 模块管理权限（待配置） |
| 租户成员 | `{tenant_id}:member` | 基础访问权限（待配置） |

## 模块同步服务

`ModuleSyncService` 负责将模块定义层的数据同步到租户实例层：

| 同步方法 | 源模型 | 目标模型 |
|----------|--------|----------|
| `sync_module_assigned` | Module* | Menu, Permission, Role, RolePermission, MenuPermission |
| `sync_module_role_permission_created` | ModuleRolePermission | RolePermission |
| `sync_module_role_permission_deleted` | ModuleRolePermission | RolePermission |
| `sync_module_menu_permission_created` | ModuleMenuPermission | MenuPermission |
| `sync_module_menu_permission_deleted` | ModuleMenuPermission | MenuPermission |

### 同步映射规则

```
模块定义层                          租户实例层
────────────                       ────────────
ModuleRolePermission.module_role_id    → Role.ref_id
ModuleRolePermission.module_permission_id → Permission.ref_id
ModuleMenuPermission.module_menu_id    → Menu.ref_id
ModuleMenuPermission.module_permission_id → Permission.ref_id
```

## 开发规则

- Controller 只处理路由、参数校验、鉴权依赖和响应封装
- Service 负责事务边界、业务校验和跨模型协作
- Organization 模型继承 `TreeNodeMixin`，树字段由 Mixin 自动维护

## 测试

```bash
uv run pytest tests/iam/ -v
```
