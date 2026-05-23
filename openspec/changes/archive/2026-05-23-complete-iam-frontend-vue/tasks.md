# IAM 前端模块完善任务清单

## 1. 权限树组件

- [x] 1.1 创建 PermissionTree.vue 组件基础结构（使用 el-tree）
- [x] 1.2 实现权限按资源分组展示（资源作为父节点）
- [x] 1.3 实现权限多选功能（v-model 双向绑定）
- [x] 1.4 实现权限搜索过滤功能
- [x] 1.5 实现 Props 接口（permissions、modelValue、disabled）
- [x] 1.6 在 RoleForm.vue 中集成权限树组件替换原有 checkbox

## 2. 部门树组件

- [x] 2.1 创建 DepartmentTree.vue 组件基础结构（使用 el-tree）
- [x] 2.2 实现部门树形结构展示
- [x] 2.3 实现节点选择功能（单选/多选模式）
- [x] 2.4 实现部门搜索过滤功能
- [x] 2.5 实现 Props 接口（departments、modelValue、mode、defaultExpandLevel）
- [x] 2.6 在 DepartmentPage.vue 中集成部门树组件

## 3. 登录历史功能

- [x] 3.1 创建 LoginHistory 类型定义
- [x] 3.2 扩展 api/auth.ts 添加 getLoginHistory 方法
- [x] 3.3 在 Profile.vue 中添加登录历史 Tab 页签
- [x] 3.4 实现登录历史列表展示（el-table）
- [x] 3.5 实现分页功能
- [x] 3.6 实现时间范围筛选功能

## 4. Framework 集成 - 侧边栏菜单

- [x] 4.1 定义 IAM 模块菜单配置（用户管理、角色管理、部门管理、租户管理、权限管理）
- [x] 4.2 修改 AppSidebar.vue 支持动态菜单渲染
- [x] 4.3 实现菜单权限过滤逻辑
- [x] 4.4 实现子菜单展开/折叠功能
- [x] 4.5 添加 IAM 模块菜单图标

## 5. Framework 集成 - 租户上下文

- [x] 5.1 扩展 UserInfo 类型（添加 tenantId、tenantName、tenantCode、tenants 字段）
- [x] 5.2 修改 useUserStore 添加 currentTenant computed 属性
- [x] 5.3 修改 useUserStore 添加 tenants 列表存储
- [x] 5.4 修改登录流程获取并存储租户信息
- [x] 5.5 在 AppNavbar.vue 中添加租户显示和切换下拉框

## 6. Framework 集成 - 权限指令

- [x] 6.1 在 main.ts 中注册 v-permission 指令
- [x] 6.2 确保 PermissionStore 在登录后加载权限数据
- [x] 6.3 创建 usePermission composable（hasPermission、hasAnyPermission、hasAllPermissions）
- [x] 6.4 在 IAM 模块页面中应用权限指令示例

## 7. API 单元测试

- [x] 7.1 创建 tests/iam/api/auth.test.ts 测试文件
- [x] 7.2 创建 tests/iam/api/user.test.ts 测试文件
- [x] 7.3 创建 tests/iam/api/role.test.ts 测试文件
- [x] 7.4 创建 tests/iam/api/department.test.ts 测试文件
- [x] 7.5 创建 tests/iam/api/tenant.test.ts 测试文件
- [x] 7.6 创建 tests/iam/api/permission.test.ts 测试文件

## 8. Store 单元测试

- [x] 8.1 创建 tests/iam/stores/auth.test.ts 测试文件
- [x] 8.2 创建 tests/iam/stores/user.test.ts 测试文件
- [x] 8.3 创建 tests/iam/stores/role.test.ts 测试文件
- [x] 8.4 创建 tests/iam/stores/department.test.ts 测试文件
- [x] 8.5 创建 tests/iam/stores/tenant.test.ts 测试文件

## 9. 组件测试

- [x] 9.1 创建 tests/iam/components/PermissionTree.test.ts 测试文件
- [x] 9.2 创建 tests/iam/components/DepartmentTree.test.ts 测试文件
- [x] 9.3 创建 tests/iam/components/UserForm.test.ts 测试文件

## 10. 性能优化

- [x] 10.1 为权限树组件实现虚拟滚动（大数据量场景）
- [x] 10.2 为部门树组件实现懒加载子节点
- [x] 10.3 优化用户列表页面的分页加载性能
- [x] 10.4 添加防抖搜索优化
