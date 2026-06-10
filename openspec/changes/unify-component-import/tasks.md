## 1. 创建统一组件入口

- [x] 1.1 创建 `web/vue/src/components/index.ts` 统一入口文件
- [x] 1.2 实现 common 组件导出（Button, Input, Card, Select, Table, Tree, TreeList, CheckboxTree, Loading, Modal, MessageBox, SmartTooltip, Pagination, DateInput, TreeSelect, DescriptionList, DataTable, DataTablePagination）
- [x] 1.3 实现高频 ui 组件重导出（Badge, Skeleton, Label, Checkbox, Switch, Textarea, Dialog 全套, Tabs 全套, Form 全套）
- [x] 1.4 实现类型定义导出（TreeSelectProps, DescriptionItem, DataTableState, MessageBoxOptions 等）

## 2. 迁移 tenant 模块

- [x] 2.1 迁移 `tenant/pages/tenants/TenantList.vue`
- [x] 2.2 迁移 `tenant/pages/tenants/TenantForm.vue`
- [x] 2.3 迁移 `tenant/pages/tenants/TenantDetail.vue`
- [x] 2.4 迁移 `tenant/pages/admin/ModuleList.vue`
- [x] 2.5 迁移 `tenant/pages/admin/ModuleForm.vue`
- [x] 2.6 迁移 `tenant/pages/admin/ModuleDetail.vue`
- [x] 2.7 迁移 `tenant/pages/admin/ResourceConfigList.vue`
- [x] 2.8 迁移 `tenant/pages/admin/AdminLoginPage.vue`
- [x] 2.9 迁移 `tenant/components/AdminSidebar.vue`（无需迁移：仅 sidebar 低频组件）
- [x] 2.10 迁移 `tenant/components/NavMain.vue`（无需迁移：仅 collapsible/sidebar 低频组件）
- [x] 2.11 迁移 `tenant/components/NavUser.vue`（无需迁移：仅 avatar/dropdown/sidebar 低频组件）
- [x] 2.12 迁移 `tenant/layouts/AdminConsoleLayout.vue`（无需迁移：仅 breadcrumb/separator/sidebar 低频组件）

## 3. 迁移 iam 模块

- [x] 3.1 迁移 `iam/pages/users/UserList.vue`
- [x] 3.2 迁移 `iam/pages/users/UserForm.vue`
- [x] 3.3 迁移 `iam/pages/users/UserDetail.vue`
- [x] 3.4 迁移 `iam/pages/roles/RoleList.vue`
- [x] 3.5 迁移 `iam/pages/roles/RoleForm.vue`
- [x] 3.6 迁移 `iam/pages/permissions/PermissionList.vue`
- [x] 3.7 迁移 `iam/pages/menus/MenuList.vue`
- [x] 3.8 迁移 `iam/pages/departments/DepartmentPage.vue`
- [x] 3.9 迁移 `iam/pages/profile/Profile.vue`
- [x] 3.10 迁移 `iam/components/PermissionAssignDialog.vue`
- [x] 3.11 迁移 `iam/components/MenuTree.vue`

## 4. 迁移 demo 模块

- [x] 4.1 迁移 `demo/pages/DatasetsPage.vue`
- [x] 4.2 迁移 `demo/pages/HealthPage.vue`
- [x] 4.3 迁移 `demo/pages/EventBusDemoPage.vue`
- [x] 4.4 迁移 `demo/pages/HomePage.vue`（无需迁移：仅 Card 手动组装 + AppPage）

## 5. 迁移 framework 模块

- [x] 5.1 迁移 `framework/pages/LoginPage.vue`
- [x] 5.2 迁移 `framework/pages/PreviewLayoutPage.vue`
- [x] 5.3 迁移 `framework/pages/NotFoundPage.vue`
- [x] 5.4 迁移 `framework/pages/ForbiddenPage.vue`
- [x] 5.5 迁移 `framework/layouts/AdminLayout.vue`（无需迁移：仅 sidebar 低频组件）
- [x] 5.6 迁移 `framework/layouts/components/AppNavMain.vue`（无需迁移：仅 collapsible/sidebar）
- [x] 5.7 迁移 `framework/layouts/components/AppTenantSwitcher.vue`（无需迁移：仅 dropdown/sidebar）
- [x] 5.8 迁移 `framework/layouts/components/AppContentHeader.vue`（无需迁移：仅 sidebar/separator/breadcrumb）
- [x] 5.9 迁移 `framework/layouts/components/AppHeaderRight.vue`
- [x] 5.10 迁移 `framework/layouts/components/AppNotificationPanel.vue`
- [x] 5.11 迁移 `framework/layouts/components/AppNavbar.vue`
- [x] 5.12 迁移 `framework/components/CommandPalette.vue`

## 6. 迁移 ai 模块

- [x] 6.1 迁移 `ai/pages/ConversationListPage.vue`
- [x] 6.2 迁移 `ai/pages/ChatPage.vue`
- [x] 6.3 迁移 `ai/components/ModelSelector.vue`

## 7. 更新文档和 memory 约束

- [x] 7.1 更新 `web/vue/src/CLAUDE.md`：组件导入规范章节（统一入口说明、组件清单、查找优先级）
- [x] 7.2 更新 `web/vue/src/components/common/CLAUDE.md`：导入方式章节（推荐从 `@/components` 导入）
- [x] 7.3 写入 memory 文件 `component-import-priority.md`：记录统一入口规则、同名组件映射、低频组件清单

## 8. 验证

- [x] 8.1 运行 `pnpm dev` 验证开发模式启动正常
- [x] 8.2 运行 `pnpm build` 验证生产构建成功
- [ ] 8.3 运行 `pnpm test:unit` 验证所有单元测试通过
