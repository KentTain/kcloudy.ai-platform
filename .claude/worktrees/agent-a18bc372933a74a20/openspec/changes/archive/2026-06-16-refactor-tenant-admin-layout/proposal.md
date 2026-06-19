## 为什么

当前 Tenant 模块的管理后台布局 (`AdminConsoleLayout`) 存在三个问题：
1. **命名不统一**：与 Framework 模块的 `AdminLayout` 体系不一致（`Admin` vs `App` 前缀混用，`Console` 后缀冗余）
2. **组件目录层级混乱**：布局子组件（`NavMain`、`NavUser`、`AdminSidebar`）散落在 `tenant/components/` 目录下，未遵循"布局子组件归入 `layouts/components/`"的规范
3. **菜单样式陈旧**：使用 `variant="inset"` 静态硬编码菜单，不支持折叠图标模式，且与 Framework 的动态菜单体系有视觉差距

## 变更内容

### 新建
- **后端 API**：在 `tenant_controller.py` 新增 `GET /tenant/admin/v1/admin/menus` 端点，从 `module.code='tenant'` 的 `module_menus` 获取动态菜单
- **前端 Store**：`tenant/stores/adminMenu.ts` — 管理员菜单 Store
- **前端组件**：`tenant/layouts/components/AppBrandHeader.vue` — 品牌标识组件
- **前端组件**：`tenant/layouts/components/AppNavMain.vue` — 动态菜单组件（迁移自 `tenant/components/NavMain.vue`）
- **前端组件**：`tenant/layouts/components/AppNavUser.vue` — 用户面板组件（迁移自 `tenant/components/NavUser.vue`）

### 修改
- **布局重命名**：`AdminConsoleLayout.vue` → `AdminLayout.vue`，并重构为 Framework 一致的侧边栏 `collapsible="icon"` 样式
- **路由引用更新**：`tenant/router/index.ts` 更新布局导入路径
- **Store 导出更新**：`tenant/stores/index.ts` 导出 `adminMenuStore`

### 删除
- `tenant/components/AdminSidebar.vue` — 拆解为 AppBrandHeader + AppNavMain + AppNavUser
- `tenant/components/NavMain.vue` — 迁移至 `layouts/components/AppNavMain.vue`
- `tenant/components/NavUser.vue` — 迁移至 `layouts/components/AppNavUser.vue`

## 功能 (Capabilities)

### 新增功能
- `admin-layout-ui`: Tenant 管理后台布局统一重构，包括组件命名规范化、目录结构调整、侧边栏样式对齐

### 修改功能
<!-- 无需求级变更 -->

## 影响

### 后端
- `tenant_controller.py` — 新增 1 个 API 端点

### 前端
- `tenant/layouts/AdminConsoleLayout.vue` → 重命名为 `AdminLayout.vue`，引用路径变更
- `tenant/router/index.ts` — 更新布局导入路径
- `tenant/stores/index.ts` — 新增 adminMenuStore 导出

### 破坏性变更
- 无。删除的三个组件 (`AdminSidebar`, `NavMain`, `NavUser`) 仅被 `AdminConsoleLayout` 使用，无其他引用
