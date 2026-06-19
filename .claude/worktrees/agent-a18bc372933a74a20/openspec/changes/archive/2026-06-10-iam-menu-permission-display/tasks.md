## 1. 基础设施

- [x] 1.1 创建菜单 API 模块 `web/vue/src/iam/api/menu.ts`
- [x] 1.2 创建菜单 Store `web/vue/src/iam/stores/menu.ts`
- [x] 1.3 扩展类型定义 `web/vue/src/iam/types/index.ts`（添加菜单相关类型）
- [x] 1.4 更新 API 导出 `web/vue/src/iam/api/index.ts`

## 2. 权限管理页面增强

- [x] 2.1 重构 `PermissionList.vue` 页面布局（移除 Tab 分组，改为表格布局）
- [x] 2.2 添加搜索功能（搜索框 + 实时过滤）
- [x] 2.3 添加操作类型 Badge 展示（read/write/delete 不同颜色）
- [x] 2.4 添加统计信息（权限总数、筛选结果统计）
- [x] 2.5 添加空状态展示

## 3. 菜单展示页面

- [x] 3.1 创建 `MenuTree.vue` 组件（左侧树形展示）
- [x] 3.2 创建 `MenuList.vue` 页面（左右布局：树 + 详情）
- [x] 3.3 实现菜单详情面板展示
- [x] 3.4 添加菜单页面路由配置 `web/vue/src/iam/router/index.ts`
- [x] 3.5 添加菜单页面导航入口（侧边栏）

## 4. 角色权限分配优化

- [x] 4.1 创建 `PermissionAssignDialog.vue` 组件（独立弹窗）
- [x] 4.2 实现权限选择列表（Checkbox + Badge）
- [x] 4.3 实现全选/取消全选功能
- [x] 4.4 实现已选统计显示
- [x] 4.5 在 `RoleList.vue` 添加「分配权限」按钮入口
- [x] 4.6 更新权限分配 API 调用逻辑

## 5. 验证

- [x] 5.1 运行前端构建验证 `pnpm build`
- [x] 5.2 运行类型检查 `pnpm check`
- [x] 5.3 运行单元测试 `pnpm test:unit tests/iam/unit/ --run`
- [x] 5.4 手动验证权限管理页面功能
- [x] 5.5 手动验证菜单展示页面功能
- [x] 5.6 手动验证角色权限分配弹窗功能
