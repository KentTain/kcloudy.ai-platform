## 为什么

IAM 模块下的 5 个页面使用 `@/components/ui/table` 组件展示列表数据，需要手动组装 TableHeader、TableBody、TableRow 等子组件，且缺乏内置的分页、加载状态、空状态处理。

`@/components/common/DataTable` 基于 @tanstack/vue-table 封装，提供声明式 API、内置分页、骨架屏加载、空状态展示等功能。迁移后可减少模板代码、提升开发效率、统一表格交互体验。

## 变更内容

### 修改

- **UserList.vue**: 将用户列表从封装版 Table 迁移到 DataTable
- **RoleList.vue**: 将角色成员表格从手动组装 Table 迁移到 DataTable
- **PermissionList.vue**: 将角色列表表格从手动组装 Table 迁移到 DataTable
- **DepartmentPage.vue**: 将下级组织表格和直属成员表格迁移到 DataTable
- **Profile.vue**: 将登录历史表格从手动组装 Table 迁移到 DataTable

## 功能 (Capabilities)

### 修改功能

- `iam-user-list`: 用户列表页面表格组件迁移
- `iam-role-list`: 角色管理页面成员表格迁移
- `iam-permission-list`: 权限管理页面角色表格迁移
- `iam-department-page`: 部门管理页面下级组织和成员表格迁移
- `iam-profile`: 个人中心页面登录历史表格迁移

## 影响

### 受影响的代码

- `web/vue/src/iam/pages/users/UserList.vue`
- `web/vue/src/iam/pages/roles/RoleList.vue`
- `web/vue/src/iam/pages/permissions/PermissionList.vue`
- `web/vue/src/iam/pages/departments/DepartmentPage.vue`
- `web/vue/src/iam/pages/profile/Profile.vue`

### 兼容性考虑

- DataTable 使用 `h()` 渲染函数定义列，需重写操作按钮
- 分页组件从 Pagination 迁移到 DataTablePagination（内置于 DataTable）
- 保持现有 API 调用和数据结构不变

### 风险点

- 样式一致性：DataTable 有内置样式，需验证与现有页面风格一致
- 响应式布局：部分表格嵌套在 Tabs 组件内，需确认高度计算正确
