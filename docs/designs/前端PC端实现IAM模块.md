对后端 Python IAM 模块和前端 Vue 框架的全面探索，以下是前端IAM模块的发现和设计思路：

  ---

# 后端 IAM 模块分析

## 数据模型

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                           核心实体关系                                    │
  ├─────────────────────────────────────────────────────────────────────────┤
  │                                                                         │
  │   ┌──────────┐          ┌──────────────┐                               │
  │   │  Tenant  │◄─────────│  UserTenant  │                               │
  │   │  (租户)  │   1:N    │ (用户租户关联) │                               │
  │   └──────────┘          └───────┬───────┘                               │
  │                                 │                                       │
  │                                 │ N:1                                   │
  │                                 ▼                                       │
  │   ┌──────────┐          ┌──────────────┐     ┌──────────────┐         │
  │   │   User   │◄─────────│  UserRole    │     │    Role      │         │
  │   │  (用户)  │   N:N    │ (用户角色关联) │◄────│    (角色)     │         │
  │   └──────────┘          └───────┬───────┘     └───────┬───────┘         │
  │                                 │                     │                 │
  │                                 │                     │ N:N             │
  │                                 │                     ▼                 │
  │                                 │           ┌──────────────┐           │
  │                                 │           │ RolePermission│          │
  │                                 │           │ (角色权限关联) │           │
  │                                 │           └───────┬───────┘           │
  │                                 │                   │                   │
  │                                 │                   │ 1:N               │
  │                                 │                   ▼                   │
  │                                 │           ┌──────────────┐           │
  │                                 └───────────│  Permission  │           │
  │                                   N:N       │   (权限)      │           │
  │                                              └──────────────┘           │
  │                                                                         │
  │   ┌──────────────┐          ┌─────────────────┐                         │
  │   │ Department  │◄─────────│  UserDepartment │                         │
  │   │   (部门)     │   1:N    │  (用户部门关联)   │                         │
  │   └──────────────┘          └─────────────────┘                         │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

## 角色体系

  ┌──────────────┬────────────┬──────────────────────────────────┐
  │   角色编码   │    名称    │               说明               │
  ├──────────────┼────────────┼──────────────────────────────────┤
  │ tenant_admin │ 租户管理员 │ 创建租户、管理租户级系统管理员   │
  ├──────────────┼────────────┼──────────────────────────────────┤
  │ system_admin │ 系统管理员 │ 管理本租户组织、用户、角色、权限 │
  ├──────────────┼────────────┼──────────────────────────────────┤
  │ user         │ 普通用户   │ 使用业务功能与维护个人信息       │
  └──────────────┴────────────┴──────────────────────────────────┘

## API 端点汇总

  ┌───────────────────────┬──────────────────────────────┐
  │         前缀          │             功能             │
  ├───────────────────────┼──────────────────────────────┤
  │ /admin/v1/auth/*│ 管理员登录登出               │
  ├───────────────────────┼──────────────────────────────┤
  │ /admin/v1/tenants/*   │ 租户管理（CRUD、激活、停用） │
  ├───────────────────────┼──────────────────────────────┤
  │ /api/v1/auth/*│ 用户登录、刷新 Token         │
  ├───────────────────────┼──────────────────────────────┤
  │ /api/v1/users/*       │ 用户管理                     │
  ├───────────────────────┼──────────────────────────────┤
  │ /api/v1/roles/*│ 角色管理                     │
  ├───────────────────────┼──────────────────────────────┤
  │ /api/v1/permissions/* │ 权限管理                     │
  ├───────────────────────┼──────────────────────────────┤
  │ /api/v1/departments/*│ 部门管理                     │
  ├───────────────────────┼──────────────────────────────┤
  │ /console/v1/tenants/* │ 用户端租户接口               │
  └───────────────────────┴──────────────────────────────┘

  ---

# 前端 Framework 结构

  web/vue/src/
  ├── framework/                    # 框架层
  │   ├── api/client.ts             # Axios 封装（自动处理 401/403）
  │   ├── stores/
  │   │   ├── user.ts               # 用户状态（token、userInfo、hasPermission）
  │   │   └── permission.ts         # 权限状态（菜单、路由）
  │   ├── router/index.ts           # 路由配置（静态 + 异步）
  │   ├── layouts/                  # 布局组件
  │   └── pages/LoginPage.vue       # 登录页
  │
  └── demo/                         # 示例模块
      ├── api/                      # API 客户端
      ├── pages/                    # 页面组件
      ├── router/index.ts           # 模块路由
      └── stores/                   # 状态管理

## 模块集成模式

  1. API 层: 使用 Framework 的 get/post/put/del 封装调用
  2. 路由层: 在 asyncRoutes 中注册，或独立导入合并
  3. Store 层: 使用 Pinia 管理模块状态
  4. 页面组件: 使用 Framework 的布局和 UI 组件

  ---

# IAM 前端模块设计建议

## 目录结构

  web/vue/src/iam/
  ├── api/                         # API 客户端
  │   ├── auth.ts                  # 认证 API
  │   ├── tenant.ts                # 租户 API
  │   ├── user.ts                  # 用户 API
  │   ├── role.ts                  # 角色 API
  │   ├── permission.ts            # 权限 API
  │   └── department.ts            # 部门 API
  │
  ├── components/                  # 业务组件
  │   ├── UserForm.vue             # 用户表单
  │   ├── RoleSelect.vue           # 角色选择器
  │   ├── PermissionTree.vue       # 权限树
  │   └── DepartmentTree.vue       # 部门树
  │
  ├── pages/                       # 页面组件
  │   ├── Login.vue                # 登录页（可复用或覆盖）
  │   ├── tenants/                 # 租户管理页面
  │   │   ├── TenantList.vue       # 租户列表
  │   │   └── TenantDetail.vue     # 租户详情
  │   ├── users/                   # 用户管理页面
  │   │   ├── UserList.vue         # 用户列表
  │   │   └── UserForm.vue         # 用户表单
  │   ├── roles/                   # 角色管理页面
  │   │   ├── RoleList.vue         # 角色列表
  │   │   └── RoleForm.vue         # 角色表单（包含权限分配）
  │   ├── permissions/             # 权限管理页面
  │   │   └── PermissionList.vue   # 权限列表
  │   ├── departments/             # 部门管理页面
  │   │   ├── DepartmentTree.vue  # 部门树
  │   │   └── DepartmentForm.vue  # 部门表单
  │   └── profile/                 # 个人中心
  │       └── Profile.vue          # 个人资料
  │
  ├── stores/                      # 状态管理
  │   ├── tenant.ts                # 租户状态
  │   ├── user.ts                  # 用户状态（可扩展现有 user store）
  │   ├── role.ts                  # 角色状态
  │   └── permission.ts            # 权限状态
  │
  ├── router/                      # 路由配置
  │   └── index.ts                 # IAM 模块路由
  │
  ├── types/                       # 类型定义
  │   └── index.ts                 # 类型（与后端 Schema 对应）
  │
  └── CLAUDE.md                    # 模块文档

## 类型映射建议

  // types/index.ts
  export interface User {
    id: string;
    username: string;
    email?: string;
    phone?: string;
    nickname?: string;
    avatar?: string;
    status: 'active' | 'inactive' | 'locked';
    profile_completed: boolean;
    is_email_verified: boolean;
    is_phone_verified: boolean;
    last_login_at?: string;
    created_at: string;
  }

  export interface Role {
    id: string;
    tenant_id?: string;
    code: string;
    name: string;
    description?: string;
    is_system: boolean;
    created_at: string;
  }

  export interface Permission {
    id: string;
    code: string;
    name: string;
    resource: string;
    action: string;
    description?: string;
  }

  export interface Department {
    id: string;
    tenant_id: string;
    parent_id?: string;
    name: string;
    code?: string;
    sort_order: number;
    leader_id?: string;
    status: 'active' | 'inactive';
    children?: Department[];
  }

  export interface Tenant {
    id: string;
    name: string;
    code: string;
    status: 'active' | 'inactive';
    contact_name?: string;
    contact_email?: string;
    contact_phone?: string;
    expired_at?: string;
  }

## 权限控制集成

  // 使用 Framework 现有的权限指令
  <button v-permission="'user:add'">添加用户</button>
  <button v-permission="['user:edit', 'user:delete']">操作</button>

  // 使用 Store 权限检查
  import { useUserStore } from "@/framework/stores";
  const userStore = useUserStore();
  userStore.hasPermission("user:delete");
  userStore.hasRole("tenant_admin");

## 路由守卫

  根据角色动态生成菜单和路由：

- tenant_admin: 租户管理、用户管理、角色管理、部门管理、权限管理
- system_admin: 用户管理、角色管理、部门管理、权限管理
- user: 个人中心

  ---

# 关键集成点

  1. 登录认证: 复用 /framework/pages/LoginPage.vue，调用 /api/v1/auth/login
  2. Token 管理: 使用 localStorage + Framework 的 user.ts store
  3. 租户上下文: 通过 HTTP Header X-Tenant-Id 传递（后端中间件解析）
  4. 动态路由: 使用 permission.ts 的 generateRoutes 方法
  5. 菜单集成: 在侧边栏组件中根据用户角色渲染菜单项

  ---
