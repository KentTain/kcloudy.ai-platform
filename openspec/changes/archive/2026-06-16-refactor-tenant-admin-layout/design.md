## 上下文

### 当前状态

Tenant 模块的管理后台布局 (`AdminConsoleLayout`) 采用独立于 Framework 的设计：

- 左侧侧边栏使用 `variant="inset"`，不支持折叠图标模式
- 菜单数据为前端硬编码的三个静态项（租户管理、资源配置、模块管理）
- 布局子组件分散在 `tenant/components/` 目录下
- 组件使用 `Admin` 前缀命名，与 Framework 的 `App` 前缀体系不一致

Framework 模块的 `AdminLayout` 已实现了一套成熟的布局体系：
- 侧边栏 `collapsible="icon" variant="sidebar"` 支持图标折叠模式
- 菜单数据从后端动态获取，支持分组与子菜单
- 布局子组件统一归入 `layouts/components/` 目录
- 使用 `App` 前缀统一命名

### 约束

- 后端已存在 `Module`、`ModuleMenu` 模型与 `ModuleMenuService`（含 `build_tree` 方法）
- Tenant 管理员走独立的 `AdminAuthMiddleware` 认证体系（`admin_token`）
- 侧边栏顶部保留品牌标识（Logo + KCloudy / 管理后台），不使用 Framework 的租户切换器
- 用户面板保留在侧边栏底部，但样式对齐 Framework
- 菜单数据从 `module.code='tenant'` 的 `module_menus` 动态获取

## 目标 / 非目标

**目标：**
- 统一 Tenent 管理后台布局命名规范（`AdminConsoleLayout` → `AdminLayout`，组件使用 `App` 前缀）
- 调整组件目录层级（布局子组件 → `layouts/components/`）
- 侧边栏样式对齐 Framework（`collapsible="icon" variant="sidebar"`）
- 实现菜单从后端动态获取（Tenant 模块的 `module_menus`）
- 用户面板保留底部但样式对齐 Framework
- 品牌标识保留顶部但样式优化

**非目标：**
- 不改变 Tenant 管理后台的路由结构
- 不引入 Framework 的 `AppTenantSwitcher` / `AppSearchBox` / `AppHeaderRight` 等组件
- 不修改 Framework 的现有布局组件
- 不涉及权限体系的变更
- 不涉及数据库迁移（后端已有表结构）

## 决策

### D1：菜单 API 设计 → 在 tenant_controller.py 中新增端点

- **方案 A（采用）**：在 `tenant/controllers/admin/tenant_controller.py` 中新增 `GET /admin/menus` 端点
- **理由**：
  - 路径 `/tenant/admin/v1/admin/menus`，由 `AdminAuthMiddleware` 自动认证
  - 已有 `ModuleMenuService.list_menus(module_id)` 和 `build_tree(menus)` 可直接复用
  - 通过 `module.code='tenant'` 定位模块，不增加新表
- **替代方案**：新建 `admin_menu_controller.py` → 过度拆分，功能简单，不需要独立文件

### D2：前端 Store 设计 → 新建独立的 adminMenuStore

- **方案 A（采用）**：新建 `tenant/stores/adminMenu.ts`，不使用 Framework 的 `menuStore`
- **理由**：
  - Tenant 管理员使用 `admin_token` 认证，与 Framework 的 `user_token` 体系不同
  - Framework 的 `menuStore.fetchUserMenus()` 请求 `/iam/console/v1/users/menus`，认证方式不兼容
  - 新建 Store 可保持认证上下文独立，结构简单
- **替代方案**：复用 Framework menuStore → 需要修改认证逻辑，耦合度高

### D3：组件目录重组 → 解构 AdminSidebar 为独立组件

- **方案 A（采用）**：删除 `AdminSidebar.vue`，其内容在 `AdminLayout.vue` 中直接引用三个独立子组件
- **目录结构**：
  ```
  tenant/layouts/components/
    ├── AppBrandHeader.vue    # 品牌标识（原 AdminSidebar 顶部）
    ├── AppNavMain.vue        # 动态菜单（迁移自 NavMain.vue，改造为动态数据源）
    └── AppNavUser.vue        # 用户面板（迁移自 NavUser.vue，样式对齐 Framework）
  ```
- **理由**：
  - 与 Framework 的 `layouts/components/` 结构一致
  - 组件职责单一，便于独立维护和测试

### D4：布局 Sidebar 配置 → 对齐 Framework

- **方案 A（采用）**：使用 `collapsible="icon" variant="sidebar"` 替代 `variant="inset"`
- **理由**：
  - `collapsible="icon"` 支持侧边栏折叠为图标模式，释放内容区空间
  - `variant="sidebar"` 为标准侧边栏样式，与 Framework 一致
  - inset 模式在折叠时视觉效果不一致

### D5：AppNavMain 菜单渲染逻辑 → 复用 Framework 的样式模板

- **方案 A（采用）**：新建 `AppNavMain.vue` 独立组件，渲染逻辑参考 Framework 的 `AppNavMain.vue`
- **但**：会简化处理，因为 Tenant 管理后台的菜单只有一级（如"租户管理"），暂不需要分组/折叠等复杂能力
- **数据结构映射**：
  - 后端 `ModuleMenuTreeResponse` 的 `name` → `AppNavMain` 的 `title`
  - `path` → `url`
  - `icon` → 使用 `@lucide/vue` 动态加载
  - `children` 支持二级子菜单展开

### D6：AppNavUser 样式设计 → 对齐 Framework 用户面板

- **方案 A（采用）**：参考 Framework AppHeaderRight 中用户面板的样式，但保留底部位置
- **样式对齐点**：
  - 头像：`Avatar` 使用 `rounded-lg` 和渐变背景
  - 文字：`text-sm leading-tight` 网格布局
  - DropdownMenu：`w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg`

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| 后端 `module.code='tenant'` 未找到时菜单加载失败 | Store 需处理空数据与错误状态，显示"暂无可用菜单" |
| `collapsible="icon"` 折叠后品牌标识显示不全 | 使用 shadcn 内置的 Sidebar 折叠行为，图标模式只显示 icon |
| 菜单 icon 前端可能找不到对应 Lucide 图标组件 | 使用 Framework 的动态加载方式，找不到时静默隐藏图标 |
| 路由引用路径修改可能导致页面加载失败 | `router/index.ts` 更新后需验证所有子页面路由正常 |
| 旧文件删除后可能遗漏未发现的引用 | 删除前使用 codegraph 确认没有其他引用 |
