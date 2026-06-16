## 1. 后端 API

- [x] 1.1 在 `tenant/controllers/admin/tenant_controller.py` 中新增 `GET /admin/menus` 端点，通过 `ModuleService.get_by_code('tenant')` 定位模块，调用 `ModuleMenuService.list_menus()` + `build_tree()` 返回树形菜单
- [x] 1.2 在 `tenant/schemas/admin/__init__.py` 中添加导出管理员菜单响应所需的 Schema（复用 `ModuleMenuTreeResponse`）
- [x] 1.3 验证后端 API：启动服务后通过 `curl` 测试菜单接口返回正确的树形结构

## 2. 前端 Store 与菜单 API

- [x] 2.1 新建 `tenant/stores/adminMenu.ts`，定义 `AdminMenuItem` 接口和 `useAdminMenuStore`，通过 `rawGet` 调用后端菜单 API，包含 loading 和空数据处理
- [x] 2.2 在 `tenant/stores/index.ts` 中导出 `useAdminMenuStore`

## 3. 前端布局子组件

- [x] 3.1 新建 `tenant/layouts/components/AppBrandHeader.vue`，实现品牌标识（Logo + "KCloudy / 管理后台"），支持 `collapsible="icon"` 折叠模式
- [x] 3.2 新建 `tenant/layouts/components/AppNavMain.vue`，参考 Framework `AppNavMain` 的菜单渲染样式，从 `useAdminMenuStore` 获取动态菜单数据，支持平铺菜单和二级子菜单展开
- [x] 3.3 新建 `tenant/layouts/components/AppNavUser.vue`，迁移并改造 `NavUser.vue`，样式对齐 Framework 的用户面板（头像 `rounded-lg`、下拉菜单 `min-w-56` 等）

## 4. 布局重命名与重构

- [x] 4.1 将 `AdminConsoleLayout.vue` 重命名为 `AdminLayout.vue`，重构为 `collapsible="icon" variant="sidebar"` 侧边栏，集成 AppBrandHeader + AppNavMain + AppNavUser
- [x] 4.2 更新 `tenant/router/index.ts` 中布局导入路径为 `@/tenant/layouts/AdminLayout.vue`
- [x] 4.3 删除 `tenant/components/AdminSidebar.vue`、`NavMain.vue`、`NavUser.vue`

## 5. 验证

- [x] 5.1 运行前端单元测试 `pnpm test:unit tests/tenant/unit/ --run`，确保所有测试通过
- [x] 5.2 启动开发服务器 `pnpm dev`，手动验证管理后台页面渲染正常（侧边栏折叠/展开、菜单加载、用户面板操作、子页面路由）
