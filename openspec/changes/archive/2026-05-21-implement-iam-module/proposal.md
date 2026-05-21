## Why

当前系统缺乏完整的身份与访问管理（IAM）模块。现有的租户管理（tenant）模块仅包含租户和管理员的基础数据模型，缺少用户认证、授权、组织架构等核心功能。为了支持完整的用户登录、权限控制和多租户管理场景，需要构建统一的 IAM 模块。

## What Changes

### 新增功能

- **用户认证**：本地登录（用户名/邮箱/手机号 + 密码）、OAuth2 第三方登录（微信、企微）
- **Token 管理**：JWT 双 Token 机制（Access Token + Refresh Token）+ Redis 混合模式
- **用户管理**：用户注册、信息管理、密码修改、密码重置
- **RBAC 权限**：角色（租户管理员、系统管理员、普通用户）、权限、用户-角色-权限关联
- **组织架构**：部门管理、用户-部门关联
- **OAuth 用户信息补全**：第三方登录用户首次登录引导补全密码、邮箱、手机号

### 模块迁移

- 将 `tenant` 模块的数据模型（Tenant、TenantConfig、TenantAdmin、UserTenant）迁移至 `iam` 模块
- **BREAKING**：更新相关导入路径

### 新增 API 端点

- `/api/v1/iam/*` - 用户认证相关 API（登录、登出、注册、Token 刷新等）
- `/api/v1/iam/oauth/*` - OAuth2 第三方登录 API

## Capabilities

### New Capabilities

- `iam-user-auth`: 用户认证（本地登录、登出、Token 管理）
- `iam-user-management`: 用户管理（注册、信息管理、密码管理）
- `iam-oauth`: OAuth2 第三方登录（微信、企微）
- `iam-rbac`: 角色权限控制（角色、权限、用户授权）
- `iam-organization`: 组织架构（部门管理）

### Modified Capabilities

- `tenant-admin-api`: 需要与 IAM 模块的认证体系对齐
- `tenant-user-api`: 需要与 IAM 模块的用户体系对齐
- `permission-system`: 扩展以支持后端 RBAC 权限检查

## Impact

### 代码影响

- 新增 `demo/models/iam/` 目录，包含用户、角色、权限、部门等数据模型
- 新增 `demo/controllers/iam/` 目录，包含认证、用户管理相关控制器
- 新增 `demo/services/iam/` 目录，包含认证、用户管理相关服务
- 新增 `framework/utils/crypto.py`，包含密码哈希等加密工具
- 迁移 `demo/models/tenant.py` 中的模型到 `demo/models/iam/`

### API 影响

- 新增 `/api/v1/iam/*` 端点
- 新增 `/admin/v1/iam/*` 端点（管理后台）

### 数据库影响

- 新增表：`users`、`oauth_connections`、`departments`、`user_departments`、`roles`、`permissions`、`user_roles`、`role_permissions`、`login_logs`、`operation_logs`
- 迁移表：`tenants`、`tenant_configs`、`tenant_admins`、`user_tenants`（从 tenant 模块迁移）

### 依赖影响

- 新增 Python 依赖：`bcrypt`（密码哈希）、`PyJWT`（JWT Token）
- 新增 Redis 依赖：会话存储、Token 黑名单
