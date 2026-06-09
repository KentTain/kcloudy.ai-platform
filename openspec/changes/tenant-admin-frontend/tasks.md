# 租户管理前端功能任务列表

## 1. 类型定义

- [x] 1.1 创建 `web/vue/src/tenant/types/resource.ts` 资源配置类型定义
- [x] 1.2 扩展 `web/vue/src/tenant/types/index.ts` 导出资源类型
- [x] 1.3 扩展 `web/vue/src/tenant/types/admin.ts` 添加模块管理类型定义

## 2. API 模块

- [x] 2.1 创建 `web/vue/src/tenant/api/resourceConfig.ts` 资源配置 API（5 种类型）
- [x] 2.2 创建 `web/vue/src/tenant/api/module.ts` 模块管理 API
- [x] 2.3 创建 `web/vue/src/tenant/api/tenantModule.ts` 租户模块分配 API
- [x] 2.4 更新 `web/vue/src/tenant/api/index.ts` 导出新 API

## 3. 资源配置管理页面

- [x] 3.1 创建 `web/vue/src/tenant/pages/admin/ResourceConfigList.vue` 资源配置列表页面
- [x] 3.2 实现资源配置 Tab 切换组件
- [x] 3.3 实现资源配置统计卡片
- [x] 3.4 实现资源配置 DataTable 列表展示
- [x] 3.5 创建资源配置表单弹窗（内嵌在 ResourceConfigList.vue）
- [x] 3.6 实现资源配置连通性测试功能

## 4. 模块管理页面

- [x] 4.1 创建 `web/vue/src/tenant/pages/admin/ModuleList.vue` 模块列表页面
- [x] 4.2 实现模块列表统计卡片
- [x] 4.3 实现模块 DataTable 列表展示
- [x] 4.4 创建 `web/vue/src/tenant/pages/admin/ModuleDetail.vue` 模块详情页面
- [x] 4.5 实现模块详情 Tab 切换（基本信息/菜单/权限/角色）
- [x] 4.6 创建 `web/vue/src/tenant/pages/admin/ModuleForm.vue` 模块创建/编辑表单

## 5. 模块菜单管理

- [x] 5.1 创建菜单树组件（内嵌在 ModuleDetail.vue）
- [x] 5.2 创建菜单编辑表单弹窗（内嵌在 ModuleDetail.vue）
- [x] 5.3 实现菜单树的展开/折叠功能
- [x] 5.4 实现菜单的创建、编辑、删除功能

## 6. 模块权限管理

- [ ] 6.1 创建 `web/vue/src/tenant/components/ModulePermissionList.vue` 权限列表组件
- [ ] 6.2 创建 `web/vue/src/tenant/components/ModulePermissionForm.vue` 权限编辑表单弹窗
- [ ] 6.3 实现权限的创建、编辑、删除功能

## 7. 模块角色管理

- [ ] 7.1 创建 `web/vue/src/tenant/components/ModuleRoleList.vue` 角色列表组件
- [ ] 7.2 创建 `web/vue/src/tenant/components/ModuleRoleForm.vue` 角色编辑表单弹窗
- [ ] 7.3 创建 `web/vue/src/tenant/components/RolePermissionEditor.vue` 角色权限编辑组件
- [ ] 7.4 实现角色的创建、编辑、删除功能
- [ ] 7.5 实现角色权限分配功能

## 8. 租户详情页扩展

- [ ] 8.1 更新 `web/vue/src/tenant/pages/tenants/TenantDetail.vue` 为 Tab 结构
- [ ] 8.2 创建 `web/vue/src/tenant/components/TenantResourceBinding.vue` 资源绑定 Tab 组件
- [ ] 8.3 创建 `web/vue/src/tenant/components/TenantModuleAssignment.vue` 模块分配 Tab 组件
- [ ] 8.4 实现资源绑定选择器和测试连接功能
- [ ] 8.5 实现模块分配列表和分配/取消功能

## 9. 路由配置

- [ ] 9.1 更新 `web/vue/src/tenant/router/index.ts` 添加资源配置路由
- [ ] 9.2 更新 `web/vue/src/tenant/router/index.ts` 添加模块管理路由
- [ ] 9.3 更新管理后台侧边栏菜单添加新入口

## 10. 验证

- [ ] 10.1 运行 `pnpm build` 验证构建
- [ ] 10.2 运行 `pnpm check` 验证类型检查
- [ ] 10.3 手动验证资源配置管理功能
- [ ] 10.4 手动验证模块管理功能
- [ ] 10.5 手动验证租户详情页扩展功能
