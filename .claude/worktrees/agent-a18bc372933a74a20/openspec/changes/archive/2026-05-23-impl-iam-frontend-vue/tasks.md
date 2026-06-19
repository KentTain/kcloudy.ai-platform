# IAM 前端模块实现任务清单

## 1. 基础框架搭建

- [x] 1.1 创建 IAM 模块目录结构（api, components, pages, router, stores, types）
- [x] 1.2 创建类型定义文件 types/index.ts（User, Role, Permission, Department, Tenant 等）
- [x] 1.3 创建 API 基础封装（统一响应类型、错误处理）
- [x] 1.4 创建 IAM 模块路由配置 router/index.ts
- [x] 1.5 创建 IAM Store 基类（tenant store, role store 等）
- [x] 1.6 创建模块入口文件（index.ts 导出所有）

## 2. 认证功能

- [x] 2.1 创建认证 API 封装 api/auth.ts（login, logout, refreshToken, getCurrentUser）
- [x] 2.2 创建认证 Store（useAuthStore 处理登录状态和 Token）
- [x] 2.3 集成 Framework 用户状态（扩展 user store 处理用户信息）
- [x] 2.4 实现登录页面调用认证 API
- [x] 2.5 实现登出功能并清理状态

## 3. 用户管理

- [x] 3.1 创建用户 API 封装 api/user.ts（list, get, create, update, delete, assignRole, assignDepartment）
- [x] 3.2 创建用户 Store（useUserStore 处理用户列表和操作）
- [x] 3.3 创建用户列表页面 pages/users/UserList.vue（分页、搜索、筛选）
- [x] 3.4 创建用户详情页面 pages/users/UserDetail.vue
- [x] 3.5 创建用户表单组件 pages/users/UserForm.vue（新建/编辑）
- [x] 3.6 实现用户状态管理（启用/停用/锁定）
- [x] 3.7 实现用户密码重置功能

## 4. 角色管理

- [x] 4.1 创建角色 API 封装 api/role.ts（list, get, create, update, delete, assignPermissions）
- [x] 4.2 创建角色 Store（useRoleStore 处理角色列表和操作）
- [x] 4.3 创建角色列表页面 pages/roles/RoleList.vue
- [x] 4.4 创建角色表单组件 pages/roles/RoleForm.vue（包含权限选择）
- [ ] 4.5 创建权限树组件 components/PermissionTree.vue（用于权限分配）
- [x] 4.6 实现角色权限分配功能

## 5. 权限管理

- [x] 5.1 创建权限 API 封装 api/permission.ts（list, getByResource）
- [x] 5.2 创建权限 Store（usePermissionStore 处理权限数据）
- [x] 5.3 创建权限列表页面 pages/permissions/PermissionList.vue
- [x] 5.4 实现按资源分组展示权限

## 6. 部门管理

- [x] 6.1 创建部门 API 封装 api/department.ts（list, tree, create, update, delete, setLeader, getUsers）
- [x] 6.2 创建部门 Store（useDepartmentStore 处理部门树和操作）
- [ ] 6.3 创建部门树组件 components/DepartmentTree.vue（树形展示）
- [x] 6.4 创建部门管理页面 pages/departments/DepartmentPage.vue
- [x] 6.5 实现部门 CRUD 功能
- [x] 6.6 实现部门负责人设置
- [x] 6.7 实现部门用户管理

## 7. 租户管理

- [x] 7.1 创建租户 API 封装 api/tenant.ts（admin/list, admin/get, admin/create, admin/update, admin/delete）
- [x] 7.2 创建租户 Store（useTenantStore 处理租户数据）
- [x] 7.3 创建租户列表页面 pages/tenants/TenantList.vue（管理员）
- [x] 7.4 创建租户详情页面 pages/tenants/TenantDetail.vue
- [x] 7.5 创建租户表单组件 pages/tenants/TenantForm.vue
- [x] 7.6 实现租户激活/停用功能
- [x] 7.7 实现租户切换功能（console 租户切换）

## 8. 个人中心

- [x] 8.1 创建个人中心页面 pages/profile/Profile.vue
- [x] 8.2 实现个人资料查看与修改
- [x] 8.3 实现修改密码功能
- [ ] 8.4 实现查看登录历史功能

## 9. Framework 集成

- [x] 9.1 更新 Framework 路由配置，添加 IAM 模块路由
- [ ] 9.2 更新 Framework 侧边栏菜单，集成 IAM 菜单
- [ ] 9.3 扩展用户状态，增加租户上下文信息
- [ ] 9.4 集成权限指令，支持页面内按钮级权限控制

## 10. 测试与优化

- [ ] 10.1 创建 API 单元测试
- [ ] 10.2 创建 Store 单元测试
- [ ] 10.3 创建关键页面组件测试
- [ ] 10.4 优化大数据量性能（分页、虚拟滚动）
- [x] 10.5 添加 loading 状态和错误处理
