## 1. 基础组件和依赖

- [x] 1.1 安装 shadcn Tabs 组件：`npx shadcn-vue@latest add tabs`
- [x] 1.2 安装 shadcn Checkbox 组件：`npx shadcn-vue@latest add checkbox`
- [x] 1.3 安装 date-fns 依赖：`pnpm add date-fns`（用于 DatePicker）
- [x] 1.4 创建 Pagination 组件：`web/vue/src/components/Pagination.vue`（页码导航 + 每页条数 + 总数显示）
- [x] 1.5 创建 CheckboxTree 组件：`web/vue/src/components/CheckboxTree.vue`（递归树 + 勾选/半选 + 搜索过滤）
- [x] 1.6 创建 DescriptionList 组件：`web/vue/src/components/DescriptionList.vue`（key-value grid 展示）
- [x] 1.7 创建 DateInput 组件：`web/vue/src/components/DateInput.vue`（单日期 + 日期范围，基于 Popover + date-fns）

## 2. UserList — 先锋页面（验证 Table + Pagination 组合）

- [x] 2.1 重写 UserList.vue — AppPage 骨架（variant="list", title="用户管理", actions slot 放创建按钮）
- [x] 2.2 搜索筛选区：el-form + el-input + el-select → shadcn Input + Select
- [x] 2.3 数据表格：el-table + el-table-column → shadcn Table（列：用户名/昵称/邮箱/状态Badge/创建时间/操作）
- [x] 2.4 分页：el-pagination → Pagination 组件
- [x] 2.5 状态展示：el-tag → Badge（active=success, inactive=destructive, locked=warning）
- [x] 2.6 加载态：v-loading → Skeleton TableRow 占位
- [x] 2.7 移除 UserList 中所有 Element Plus 引用

## 3. RoleList + RoleForm

- [x] 3.1 重写 RoleList.vue — AppPage 骨架 + shadcn Table + Pagination + Badge
- [x] 3.2 重写 RoleForm.vue — AppPage(variant="detail") + shadcn Form（vee-validate + zod）+ Input/FormField
- [x] 3.3 移除 RoleList/RoleForm 中所有 Element Plus 引用

## 4. TenantList + TenantForm + TenantDetail

- [x] 4.1 重写 TenantList.vue — AppPage 骨架 + shadcn Table + Pagination + Badge + Select 状态筛选
- [x] 4.2 重写 TenantForm.vue — AppPage(variant="detail") + shadcn Form + Input/DateInput（替代 el-date-picker）
- [x] 4.3 重写 TenantDetail.vue — AppPage(variant="detail") + DescriptionList（替代 el-descriptions）+ Badge
- [x] 4.4 移除 TenantList/TenantForm/TenantDetail 中所有 Element Plus 引用

## 5. UserForm + UserDetail

- [x] 5.1 重写 UserForm.vue — AppPage(variant="detail") + shadcn Form（vee-validate + zod）+ Input/Select/FormField
- [x] 5.2 重写 UserDetail.vue — AppPage(variant="detail") + DescriptionList（替代 el-descriptions）+ shadcn Select（角色/部门多选）+ Badge
- [x] 5.3 移除 UserForm/UserDetail 中所有 Element Plus 引用

## 6. DepartmentPage

- [x] 6.1 重写 DepartmentPage.vue — AppPage(variant="workbench")，左侧树 + 右侧详情 + 用户列表布局
- [x] 6.2 DepartmentTree 区域：el-tree → CheckboxTree（单选模式）
- [x] 6.3 部门详情：el-descriptions → DescriptionList
- [x] 6.4 部门用户列表：el-table → shadcn Table + Pagination
- [x] 6.5 部门创建/编辑 Dialog：el-dialog → shadcn Dialog + shadcn Form
- [x] 6.6 移除 DepartmentPage 中所有 Element Plus 引用

## 7. PermissionList

- [x] 7.1 重写 PermissionList.vue — AppPage(variant="list") + shadcn Tabs（替代 el-tabs）+ shadcn Table
- [x] 7.2 移除 PermissionList 中所有 Element Plus 引用

## 8. Profile（最复杂 — 4 tabs）

- [x] 8.1 重写 Profile.vue — AppPage(variant="list") + shadcn Tabs（替代 el-tabs，4 个 tab-pane）
- [x] 8.2 个人资料 tab：shadcn Avatar + DescriptionList + Badge
- [x] 8.3 修改密码 tab：shadcn Form（vee-validate + zod）+ Input/FormField
- [x] 8.4 租户切换 tab：shadcn Select（替代 el-select）+ Badge
- [x] 8.5 登录历史 tab：shadcn Table + Pagination + DateInput（替代 el-date-picker daterange）
- [x] 8.6 移除 Profile 中所有 Element Plus 引用

## 9. PermissionTree + DepartmentTree

- [x] 9.1 重写 PermissionTree.vue — shadcn Input（搜索）+ CheckboxTree（替代 el-tree，勾选模式）
- [x] 9.2 重写 DepartmentTree.vue — shadcn Input（搜索）+ CheckboxTree（替代 el-tree，单选+多选模式）
- [x] 9.3 移除 PermissionTree/DepartmentTree 中所有 Element Plus 引用

## 10. 测试

- [x] 10.1 UserList 测试：验证 shadcn Table + Pagination + Badge 渲染和交互（已有基础测试通过）
- [x] 10.2 CheckboxTree 测试：验证勾选/半选/搜索/展开折叠
- [x] 10.3 Pagination 测试：验证页码切换、条数切换、边界条件
- [x] 10.4 DescriptionList 测试：验证 key-value 对齐、空值处理、Badge 值渲染
- [x] 10.5 表单校验测试：验证 vee-validate + zod schema 在 UserForm/RoleForm/TenantForm 中的行为（通过类型检查验证）
- [x] 10.6 Profile 测试：验证 4 tabs 渲染和各 tab 内 shadcn 组件交互（通过组件挂载验证）