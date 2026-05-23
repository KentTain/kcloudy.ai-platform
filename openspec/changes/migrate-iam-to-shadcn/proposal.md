## Why

IAM 模块 11 个页面和 2 个树组件仍全部使用 Element Plus（el-card/el-table/el-form/el-tag/el-tree 等 23 种组件），与项目已完成的 shadcn-vue + Tailwind CSS 现代化方向不一致。AdminLayout 已迁移至 shadcn Sidebar，而 IAM 页面视觉风格仍停留在 Element Plus 时代，两套 UI 体系并存导致体验割裂。vee-validate + zod 已安装但 IAM 表单仍用 el-form rules，无法与 shadcn Form 生态衔接。

## What Changes

- **重写 11 个页面文件**：UserList、UserForm、UserDetail、RoleList、RoleForm、TenantList、TenantForm、TenantDetail、DepartmentPage、PermissionList、Profile — Element Plus 组件 → shadcn 组件
- **重写 2 个组件文件**：PermissionTree（el-tree + el-input → shadcn Input + 自写 CheckboxTree）、DepartmentTree（el-tree + el-input → shadcn Input + 自写 CheckboxTree）
- **组件映射**：el-card → AppPage/shadcn Card、el-table → shadcn Table、el-pagination → 自写 Pagination、el-form → shadcn Form（vee-validate + zod）、el-input → shadcn Input、el-select → shadcn Select、el-tag → Badge、el-button → shadcn Button、el-tree → 自写 CheckboxTree、el-descriptions → 自写 DescriptionList、el-tabs → shadcn Tabs（需安装）、el-dialog → shadcn Dialog、el-date-picker → 自写 DatePicker 或第三方、v-loading → Skeleton
- **移除 Element Plus 全局注册**（**BREAKING**）：完成后 IAM 模块不再依赖 Element Plus
- 逐页面迁移策略：先 UserList 验证 Table + Pagination 组合，再批量迁移其余

## Capabilities

### New Capabilities

- `iam-shadcn-ui`: IAM 模块 shadcn 组件化 UI 规范（涵盖所有页面和树组件的 Element Plus → shadcn 迁移需求）
- `iam-pagination`: 自写 Pagination 组件规范（替代 el-pagination）
- `iam-checkbox-tree`: 自写 CheckboxTree 组件规范（替代 el-tree，支持勾选/过滤/展开）
- `iam-description-list`: 自写 DescriptionList 组件规范（替代 el-descriptions）

### Modified Capabilities

- `iam-user-management`: 用户管理页面 UI 从 Element Plus → shadcn（UserList/UserForm/UserDetail）
- `iam-rbac`: 角色和权限页面 UI 从 Element Plus → shadcn（RoleList/RoleForm/PermissionList）
- `iam-organization`: 部门管理页面 UI 从 Element Plus → shadcn（DepartmentPage + DepartmentTree）
- `tenant-management`: 租户管理页面 UI 从 Element Plus → shadcn（TenantList/TenantForm/TenantDetail）
- `profile-management`: 个人中心页面 UI 从 Element Plus → shadcn（Profile）
- `permission-tree`: 权限树组件从 el-tree → 自写 CheckboxTree
- `framework-iam-integration`: IAM 侧边栏菜单与新壳已完成，本次无需修改（确认无 spec 级行为变更）

## Impact

- 受影响文件：`web/vue/src/iam/pages/` 下 11 个页面文件、`web/vue/src/iam/components/` 下 2 个组件文件
- 受影响依赖：移除对 Element Plus 组件的使用（全局注册可能保留供其他模块，IAM 模块自身不再 import）
- 新增依赖：shadcn Tabs（需安装 `npx shadcn-vue@latest add tabs`）、自写组件（Pagination、CheckboxTree、DescriptionList）放在 `web/vue/src/iam/components/` 或 `web/vue/src/components/`
- 路由无变化：14 条 IAM 路由保持不变
- Store/API 层不动：仅模板和 UI 组件层变更，业务逻辑完全不变
- 中高风险：大面积 UI 重写（11+2 文件），但业务逻辑不变，逐页面独立可测试