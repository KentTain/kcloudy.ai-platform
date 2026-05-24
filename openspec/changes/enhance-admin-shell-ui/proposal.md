## Why

当前项目 Admin Shell UI 功能较为基础，缺少现代化的用户体验功能。通过对比 kbhub 项目，发现以下功能值得借鉴：

1. **主题切换**：当前无暗色模式支持，影响夜间使用体验
2. **用户菜单增强**：当前用户菜单仅有退出登录，缺少账号设置等入口
3. **Header 快捷入口**：当前 Header 仅有面包屑，缺少水平导航和搜索功能
4. **命令面板**：当前无全局快速跳转功能
5. **菜单权限过滤**：当前菜单为静态配置，缺少动态权限控制

这些功能可显著提升用户体验和系统的可扩展性。

## What Changes

### P0 - 主题切换（低复杂度）
- 新增 `useColorMode` 组合式函数，基于 `@vueuse/core` 实现
- 在 `SidebarFooter` 用户菜单中添加主题切换选项
- 支持 `light` / `dark` / `system` 三种模式
- 主题偏好持久化到 localStorage

### P1 - 用户菜单增强（中复杂度）
- 扩展 `SidebarFooter` 用户下拉菜单
- 新增菜单项：账号设置、开发者设置、主题切换
- 优化用户信息展示（头像、昵称、用户名）

### P2 - Header 快捷入口（中复杂度）
- 在 `AppNavbar` 中新增 `NavigationMenu` 水平导航
- 新增快捷入口按钮（待办、通知等预留位置）
- 优化布局响应式设计

### P3 - 命令面板（高复杂度）
- 新增 `CommandPalette` 全局命令面板组件
- 支持快捷键 `Cmd/Ctrl + K` 唤起
- 支持页面快速跳转、功能搜索
- 基于现有 shadcn-vue Command 组件实现

### P4 - 菜单权限过滤（中复杂度）
- 扩展 `AppNavMain` 支持动态菜单过滤
- 新增 `useMenuPermission` 组合式函数
- 基于用户权限动态显示/隐藏菜单项

## Capabilities

### New Capabilities

- `theme-switching`: 主题切换功能，支持亮色/暗色/跟随系统三种模式
- `command-palette`: 全局命令面板，支持快速跳转和功能搜索
- `enhanced-user-menu`: 增强的用户菜单，包含账号设置、开发者设置、主题切换等入口
- `header-shortcuts`: Header 快捷入口，包含水平导航和快捷按钮
- `menu-permission-filter`: 菜单权限过滤，基于用户权限动态控制菜单可见性

### Modified Capabilities

无。所有功能均为新增，不改变现有功能的 spec 级别行为。

## Impact

### 受影响组件

| 组件 | 变更类型 | 说明 |
|------|----------|------|
| `framework/layouts/AdminLayout.vue` | 修改 | 集成主题切换和命令面板 |
| `framework/layouts/components/AppNavbar.vue` | 修改 | 新增水平导航、快捷按钮 |
| `framework/layouts/components/AppNavMain.vue` | 修改 | 支持权限过滤 |
| `framework/layouts/components/AppSidebarFooter.vue` | 新增 | 增强的用户菜单组件 |
| `framework/composables/useColorMode.ts` | 新增 | 主题切换组合式函数 |
| `framework/composables/useMenuPermission.ts` | 新增 | 菜单权限组合式函数 |
| `components/ui/command-palette/` | 新增 | 命令面板组件 |

### 依赖变更

- 新增依赖：`@vueuse/core`（用于 `useColorMode`、`useMediaQuery` 等）
- shadcn-vue 组件：Command、NavigationMenu（需通过 CLI 添加）

### 兼容性

- 所有变更向后兼容，不破坏现有功能
- 菜单权限过滤默认显示所有菜单，仅在配置后生效
