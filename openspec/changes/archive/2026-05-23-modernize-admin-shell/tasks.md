## 1. 新增 shadcn 组件

- [x] 1.1 安装 sidebar 组件：`npx shadcn-vue@latest add sidebar`
- [x] 1.2 安装 breadcrumb 组件：`npx shadcn-vue@latest add breadcrumb`
- [x] 1.3 安装 dropdown-menu 组件：`npx shadcn-vue@latest add dropdown-menu`
- [x] 1.4 安装 collapsible 组件：`npx shadcn-vue@latest add collapsible`

## 2. 新增 AppNavMain 分组菜单组件

- [x] 2.1 创建 `web/vue/src/framework/layouts/components/AppNavMain.vue`，实现分组菜单组件
- [x] 2.2 定义 NavMainGroup/NavMainItem/NavMainSub 类型接口
- [x] 2.3 使用 SidebarGroup/SidebarMenu/SidebarMenuItem 渲染分组
- [x] 2.4 使用 Collapsible 支持子菜单展开/折叠

## 3. 重写 AdminLayout

- [x] 3.1 重写 `web/vue/src/framework/layouts/AdminLayout.vue`，使用 SidebarProvider + Sidebar + SidebarInset
- [x] 3.2 Sidebar 设置 collapsible="icon" variant="inset"
- [x] 3.3 SidebarHeader 包含 Logo 区域
- [x] 3.4 SidebarContent 包含 AppNavMain
- [x] 3.5 SidebarFooter 包含用户信息
- [x] 3.6 SidebarInset 内包含 Header 和 AppMain

## 4. 删除 AppSidebar

- [x] 4.1 删除 `web/vue/src/framework/layouts/components/AppSidebar.vue`

## 5. 重写 AppNavbar 为 Header

- [x] 5.1 重写 `web/vue/src/framework/layouts/components/AppNavbar.vue`，使用 SidebarTrigger + Breadcrumb + DropdownMenu
- [x] 5.2 Header 高度设为 56px（3.5rem）
- [x] 5.3 左侧：SidebarTrigger + Breadcrumb
- [x] 5.4 右侧：用户 DropdownMenu

## 6. 删除 AppTagsView

- [x] 6.1 删除 `web/vue/src/framework/layouts/components/AppTagsView.vue`
- [x] 6.2 删除 `web/vue/src/framework/stores/tagsview.ts`
- [x] 6.3 从 AdminLayout 移除 AppTagsView 引用

## 7. 简化 app.ts Store

- [x] 7.1 移除 `sidebarCollapsed` ref
- [x] 7.2 移除 `toggleSidebar()` 方法
- [x] 7.3 移除 `setSidebarCollapsed()` 方法
- [x] 7.4 移除 `setDevice()` 方法和 MOBILE_BREAKPOINT 常量
- [x] 7.5 保留 `device` 作为只读 computed（基于 window.innerWidth）

## 8. 测试

- [x] 8.1 更新 `web/vue/tests/framework/components/layout.test.ts`，测试 AdminLayout 新结构
- [x] 8.2 测试 AppNavMain 分组菜单渲染
- [x] 8.3 删除 responsive.test.ts（响应式由 shadcn Sidebar 内置处理）

## 9. 文档更新

- [x] 9.1 更新 `web/vue/src/framework/CLAUDE.md`，更新布局组件章节（删除 TagsView、新增 AppNavMain）
- [x] 9.2 更新 `openspec/specs/admin-layout/spec.md`，同步删除 TagsView 需求
