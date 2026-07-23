# IAM 模块开发指南

本文件为 Claude Code 在 `web/vue/src/iam/` 身份认证与访问管理模块中工作时提供指导。

## 模块定位

IAM 模块提供身份认证与访问管理功能，包括用户管理、角色管理、权限管理、组织管理、菜单管理。与后端 `server/python/src/iam/` 模块对齐。

## 目录职责

| 目录 | 职责 |
|------|------|
| api/ | API 函数（认证、用户、角色、权限、组织、菜单） |
| components/ | 模块专用组件（OrganizationTree、PermissionTree、MenuTree） |
| layouts/ | 模块布局组件（IAMLayout） |
| pages/ | 页面组件（用户、角色、权限、组织、菜单、个人中心） |
| router/ | 模块路由配置 |
| stores/ | Pinia 状态管理（认证、用户、角色、权限、组织、菜单） |
| types/ | TypeScript 类型定义 |

## 页面组件

| 页面 | 路径 | 功能 |
|------|------|------|
| UserList | /iam/users | 用户列表管理 |
| UserForm | /iam/users/create, /iam/users/:id/edit | 用户创建/编辑 |
| UserDetail | /iam/users/:id | 用户详情查看 |
| RoleList | /iam/roles | 角色列表管理 |
| RoleForm | /iam/roles/create, /iam/roles/:id | 角色创建/编辑 |
| PermissionList | /iam/permissions | 权限列表查看 |
| OrganizationPage | /iam/organizations | 组织树形管理 |
| MenuList | /iam/menus | 菜单树形展示与详情 |
| NotificationList | /iam/notifications | 站内信列表 |
| PermissionRequestList | /iam/permission-requests | 权限申请列表 |
| PolicyList | /iam/policies | 企业策略管理 |
| Profile | /iam/profile | 个人中心 |

## 路由配置

| 路径 | 组件 | 权限 |
|------|------|------|
| /iam/users | UserList | requiresAuth |
| /iam/users/create | UserForm | requiresAuth |
| /iam/users/:id | UserDetail | requiresAuth |
| /iam/users/:id/edit | UserForm | requiresAuth |
| /iam/roles | RoleList | requiresAuth |
| /iam/roles/create | RoleForm | requiresAuth |
| /iam/roles/:id | RoleForm | requiresAuth |
| /iam/permissions | PermissionList | requiresAuth |
| /iam/organizations | OrganizationPage | requiresAuth |
| /iam/menus | MenuList | requiresAuth |
| /iam/notifications | NotificationList | requiresAuth |
| /iam/permission-requests | PermissionRequestList | requiresAuth |
| /iam/policies | PolicyList | requiresAuth |
| /iam/profile | Profile | requiresAuth |

## API 函数

### 认证 API

| 函数 | 说明 |
|------|------|
| login | 用户登录 |
| logout | 用户登出 |
| refreshToken | 刷新 Token |
| getCurrentUser | 获取当前用户信息 |
| updateProfile | 更新当前用户资料 |
| changePassword | 修改密码 |
| getLoginHistory | 获取登录历史 |

### 用户管理 API

| 函数 | 说明 |
|------|------|
| getUsers | 获取用户列表（分页） |
| getUser | 获取用户详情 |
| createUser | 创建用户 |
| updateUser | 更新用户信息 |
| deleteUser | 删除用户 |
| resetUserPassword | 重置用户密码 |
| updateUserStatus | 更新用户状态 |
| disableUser | 停用用户 |
| enableUser | 激活用户 |
| lockUser | 锁定用户 |
| assignUserRoles | 分配用户角色 |
| assignUserOrganizations | 分配用户组织 |

### 角色管理 API

| 函数 | 说明 |
|------|------|
| getRoles | 获取角色列表 |
| getRole | 获取角色详情 |
| createRole | 创建角色 |
| updateRole | 更新角色 |
| deleteRole | 删除角色 |

### 权限管理 API

| 函数 | 说明 |
|------|------|
| getPermissions | 获取权限列表 |
| getPermission | 获取权限详情 |

### 组织管理 API

| 函数 | 说明 |
|------|------|
| getOrganizations | 获取组织列表 |
| getOrganizationTree | 获取组织树形结构 |
| getOrganization | 获取组织详情 |
| createOrganization | 创建组织 |
| updateOrganization | 更新组织 |
| deleteOrganization | 删除组织 |

### 菜单管理 API

| 函数 | 说明 |
|------|------|
| getMenus | 获取菜单树（全部） |

### 站内信 API

| 函数 | 说明 |
|------|------|
| getNotifications | 获取通知列表 |
| markAsRead | 标记通知已读 |
| markAllAsRead | 全部标记已读 |
| getUnreadCount | 获取未读数量 |

### 权限申请 API

| 函数 | 说明 |
|------|------|
| getPermissionRequests | 获取权限申请列表 |
| createPermissionRequest | 创建权限申请 |
| approvePermissionRequest | 审批通过 |
| rejectPermissionRequest | 审批拒绝 |

### 企业策略 API

| 函数 | 说明 |
|------|------|
| getPolicies | 获取策略列表 |
| getPolicy | 获取策略详情 |
| createPolicy | 创建策略 |
| updatePolicy | 更新策略 |
| deletePolicy | 删除策略 |

## 核心类型

| 类型 | 说明 |
|------|------|
| User | 用户信息 |
| Role | 角色信息 |
| Permission | 权限信息 |
| Organization | 组织信息（支持树形结构） |
| MenuTreeNode | 菜单树节点信息 |
| Notification | 站内信信息 |
| PermissionRequest | 权限申请信息 |
| Policy | 企业策略信息 |
| LoginRequest | 登录请求 |
| LoginResponse | 登录响应（含 Token） |

## 开发规则

- 使用 `<script setup lang="ts">` 语法
- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore`
- 页面使用 `AppPage` 组件作为骨架
- 所有路由需要认证（requiresAuth: true）

## 测试

```bash
pnpm test:unit tests/iam/unit/ --run
```
