## 1. Profile 页面迁移

- [x] 1.1 将 Profile.vue 登录历史表格迁移到 DataTable
  - 定义 `ColumnDef<LoginHistory>[]` 列配置
  - 使用 `useDataTable` 初始化表格
  - 保留日期筛选功能
  - 移除手动组装的 Table 组件和独立 Pagination

## 2. PermissionList 页面迁移

- [x] 2.1 将 PermissionList.vue 角色列表表格迁移到 DataTable
  - 定义 `ColumnDef<Role>[]` 列配置
  - 使用 `useDataTable` 初始化表格
  - 操作按钮使用 `h()` 函数渲染
  - 移除手动组装的 Table 组件

## 3. RoleList 页面迁移

- [x] 3.1 将 RoleList.vue 角色成员表格迁移到 DataTable
  - 定义 `ColumnDef<RoleMember>[]` 列配置
  - 使用 `useDataTable` 初始化表格
  - 操作按钮（移除成员）使用 `h()` 函数渲染
  - 保持 Tab 内嵌布局正确

## 4. UserList 页面迁移

- [x] 4.1 将 UserList.vue 用户列表迁移到 DataTable
  - 定义 `ColumnDef<User>[]` 列配置
  - 使用 `useDataTable` 初始化表格，支持筛选参数
  - 操作按钮（编辑、启用/停用、重置密码、删除）使用 `h()` 函数渲染
  - 移除独立 Pagination 组件
  - 保持统计卡片区域不变

## 5. DepartmentPage 页面迁移

- [x] 5.1 将 DepartmentPage.vue 下级组织表格迁移到 DataTable
  - 定义 `ColumnDef<Department>[]` 列配置
  - 使用 `useDataTable` 初始化表格

- [x] 5.2 将 DepartmentPage.vue 直属成员表格迁移到 DataTable
  - 定义 `ColumnDef<DepartmentUser>[]` 列配置
  - 使用 `useDataTable` 初始化表格
  - 操作按钮（启用/停用/移除）使用 `h()` 函数渲染

## 6. 验证与清理

- [x] 6.1 验证所有页面功能正常
  - 验证分页功能
  - 验证筛选功能
  - 验证行内操作
  - 验证加载状态和空状态展示

- [x] 6.2 清理无用代码
  - 移除未使用的 Table 组件导入
  - 移除未使用的 Pagination 组件导入
