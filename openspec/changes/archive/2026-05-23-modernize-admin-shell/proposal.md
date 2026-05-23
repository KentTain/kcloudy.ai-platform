## Why

当前 `web/vue/src/framework/layouts/` 的 AdminLayout、AppSidebar、AppNavbar 是手写实现的布局组件，存在以下问题：
1. AppSidebar.vue 有 320+ 行手写样式和逻辑，维护成本高
2. 移动端响应式需要手动判断 `setDevice("mobile")`，代码冗余
3. 缺少分组菜单模型，菜单硬编码在组件内部
4. TagsView 在现代工作台风格中显得冗余（用户确认删除）

shadcn-vue 的 Sidebar 组件体系提供了完整的 SidebarProvider/Sidebar/SidebarInset 组合，内置响应式、折叠、移动端 Sheet 等功能，可以大幅简化布局代码。

## What Changes

- **重写 AdminLayout.vue**：替换为 SidebarProvider + Sidebar + SidebarInset 组合
- **重写 AppSidebar.vue**：替换为 shadcn SidebarHeader/Content/Footer + 分组菜单组件
- **新增 AppNavMain.vue**：分组菜单组件，支持 NavMainGroup 类型
- **重写 AppNavbar.vue**：替换为 Header（SidebarTrigger + Breadcrumb + 用户下拉）
- **删除 AppTagsView.vue**：移除标签页功能
- **简化 app.ts store**：移除 sidebarCollapsed、toggleSidebar、setDevice 等手动状态管理
- **新增 shadcn 组件**：Sidebar 系列、Breadcrumb 系列、DropdownMenu、NavigationMenu

## Capabilities

### Modified Capabilities

- `admin-layout`: 升级布局组件为 shadcn Sidebar 体系，删除 TagsView，使用 icon 折叠模式

### New Capabilities

- `app-nav-main`: 分组菜单组件，支持图标、标题、子菜单、折叠展开

## Impact

- 重写文件：AdminLayout.vue、AppSidebar.vue、AppNavbar.vue、app.ts
- 删除文件：AppTagsView.vue、tagsview.ts store
- 新增文件：AppNavMain.vue
- 新增 shadcn 组件：sidebar、breadcrumb、dropdown-menu、navigation-menu
- 所有使用 AdminLayout 的页面无需改动（壳结构对外接口不变）
- 影响 app store 的使用者（需迁移到 shadcn Sidebar 内置状态）