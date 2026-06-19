# IAM 前端模块实现提案

## Why

当前项目后端已实现完整的 IAM（身份认证与访问管理）模块，包含租户、用户、角色、权限、组织架构等功能，但前端仅有基础的登录页面。为了提供完整的用户管理和管理后台功能，需要基于后端 API 实现 Vue 前端 IAM 模块，实现与后端功能对应的 PC 端管理界面。

## What Changes

- 创建 `web/vue/src/iam/` 模块目录结构
- 实现租户管理页面（租户列表、详情、创建、编辑、启用/停用）
- 实现用户管理页面（用户列表、详情、创建、编辑、分配角色/部门）
- 实现角色管理页面（角色列表、创建、编辑、权限分配）
- 实现权限管理页面（权限列表、按资源分组展示）
- 实现部门管理页面（部门树形结构、创建、编辑、负责人设置）
- 实现个人中心页面（个人资料、修改密码）
- 集成现有 Framework 框架（权限指令、路由守卫、状态管理）
- 实现登录认证功能（登录、登出、Token 刷新）

## Capabilities

### New Capabilities

- `tenant-management`: 租户管理功能，支持租户的 CRUD 操作、激活/停用、配置管理
- `user-management`: 用户管理功能，支持用户的 CRUD、状态管理、角色/部门分配
- `role-permission-management`: 角色与权限管理，支持角色 CRUD、权限分配、权限树展示
- `department-management`: 部门管理功能，支持树形部门结构、负责人设置、用户关联
- `authentication`: 用户认证功能，支持登录、登出、Token 刷新、密码修改
- `profile-management`: 个人中心功能，支持个人资料查看与修改、密码修改

### Modified Capabilities

- 无

## Impact

### 受影响的代码

- `web/vue/src/framework/` - 需要扩展用户状态和权限状态
- `web/vue/src/router/` - 需要添加 IAM 模块路由
- 新增 `web/vue/src/iam/` - IAM 模块完整实现

### 受影响的 API

| API 端点 | 功能 |
|----------|------|
| `/api/v1/auth/*` | 登录、登出、Token 刷新 |
| `/admin/v1/tenants/*` | 租户管理（需要新增管理后台页面） |
| `/api/v1/users/*` | 用户管理 |
| `/api/v1/roles/*` | 角色管理 |
| `/api/v1/permissions/*` | 权限管理 |
| `/api/v1/departments/*` | 部门管理 |
| `/console/v1/tenants/*` | 租户切换 |

### 依赖

- 后端 Python IAM 模块已完整实现
- Framework 框架已提供基础布局、路由、权限控制
- Element Plus UI 组件库
