## 为什么

IAM 模块当前缺乏直观的菜单和权限展示功能。参照 Tenant 模块 `ModuleDetail.vue` 中菜单管理和权限管理的优秀交互体验，需要在 IAM 模块中增强现有页面的展示能力，提供更好的用户体验。

当前问题：
- 权限列表页面功能单一，无搜索、无统计、操作类型展示不直观
- 缺少独立的菜单展示页面，用户无法直观查看当前租户可用的菜单结构
- 角色权限分配交互不够友好，缺乏全选、统计等辅助功能

## 变更内容

### 新增功能
1. **权限管理页面增强** - 添加搜索框、操作类型 Badge 展示、统计信息
2. **菜单展示页面** - 新增独立的菜单展示页面，左侧树形展示 + 右侧详情
3. **角色权限分配优化** - 独立弹窗、全选/取消、已选统计、操作类型 Badge

### 修改功能
- 重构 `PermissionList.vue` 页面布局和交互
- 优化 `RoleList.vue` 中的权限分配入口和弹窗交互
- 新增菜单 API 和 Store

## 功能 (Capabilities)

### 新增功能
- `iam-permission-display`: 权限管理页面增强（搜索过滤、操作类型 Badge、统计信息展示）
- `iam-menu-display`: 菜单展示页面（树形展示、菜单详情查看、按模块分组）
- `role-permission-dialog`: 角色权限分配弹窗优化（独立弹窗、全选/取消、已选统计）

### 修改功能
- `role-permission-management`: 权限分配交互从表单内嵌改为独立弹窗

## 影响

### 前端变更
- `web/vue/src/iam/pages/permissions/PermissionList.vue` - 重构
- `web/vue/src/iam/pages/menus/MenuList.vue` - 新增
- `web/vue/src/iam/pages/roles/RoleList.vue` - 增强
- `web/vue/src/iam/components/MenuTree.vue` - 新增
- `web/vue/src/iam/components/PermissionAssignDialog.vue` - 新增
- `web/vue/src/iam/api/menu.ts` - 新增
- `web/vue/src/iam/stores/menu.ts` - 新增
- `web/vue/src/iam/types/index.ts` - 扩展
- `web/vue/src/iam/router/index.ts` - 扩展

### API 依赖
- `GET /v1/iam/menu` - 获取所有菜单（已存在）
- `GET /v1/iam/permission/grouped` - 获取分组权限（已存在）

### 无破坏性变更
本次变更仅涉及前端 UI 增强，不影响现有 API 接口和后端逻辑。
