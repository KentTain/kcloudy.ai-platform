## Context

当前 `web/vue/src/framework/layouts/` 提供了 AdminLayout、AppSidebar、AppNavbar、AppTagsView、AppMain 五个布局组件：
- AdminLayout.vue：手写 fixed sidebar + navbar + tagsview + main 布局
- AppSidebar.vue：320+ 行手写样式/逻辑/硬编码 SVG 图标
- AppNavbar.vue：手写面包屑 + 用户头像
- AppTagsView.vue：传统后台标签页
- app.ts store：手动管理 sidebarCollapsed、device 状态

shadcn-vue 已集成完成（Change #1），提供完整的 Sidebar 组件体系，可以大幅简化布局代码。

**约束**：
- 保留 AdminLayout.vue 入口和现有的路由/权限架构
- 保留 AppMain.vue（只做微调）
- 使用 icon 折叠模式（collapsible="icon"）
- 删除 TagsView（用户确认）

## Goals / Non-Goals

**Goals:**
- 使用 shadcn SidebarProvider/Sidebar/SidebarInset 重写 AdminLayout
- 使用 shadcn SidebarHeader/Content/Footer + AppNavMain 重写 AppSidebar
- 使用 shadcn SidebarTrigger/Breadcrumb/DropdownMenu 重写 AppNavbar
- 删除 TagsView 功能
- 简化 app.ts store，移除手动状态管理

**Non-Goals:**
- 不改变路由架构和权限控制逻辑
- 不改变菜单数据结构（继续使用现有的菜单配置）
- 不添加命令搜索框（属于后续增强）

## Decisions

### 决策 1: Sidebar collapsible 模式

**选择**: `icon`（折叠成图标列）

**原因**: 用户明确指定。icon 模式下侧边栏折叠时保留图标列（宽度约 48-64px），用户可以快速识别和点击菜单，比完全隐藏的 offcanvas 模式更适合后台管理系统。

**备选**: `offcanvas`（完全隐藏）

### 决策 2: TagsView 处理

**选择**: 删除

**原因**: 用户明确指定。现代工作台风格不需要传统后台的标签页导航，面包屑 + 侧边栏已足够。删除后代码更简洁。

**备选**: 弱化保留（增加复杂度）

### 决策 3: 菜单分组模型

**选择**: 新增 AppNavMain.vue 组件，支持 NavMainGroup 类型

```typescript
interface AppNavGroup {
  title?: string;
  items: Array<AppNavItem | AppNavSub>;
}

interface AppNavItem {
  icon?: FunctionalComponent;
  title: string;
  url: string;
}

interface AppNavSub {
  icon?: FunctionalComponent;
  title: string;
  items: AppNavSubItem[];
}
```

**原因**: 借鉴 kbhub NavMain 模型，支持分组标题和子菜单，比当前硬编码菜单更灵活。

### 决策 4: Header 高度

**选择**: 56px（3.5rem）

**原因**: 与 shadcn Sidebar 默认设计一致，与 Change #1 AppPage 的高度计算 `calc(100svh - 3.5rem)` 匹配。

### 决策 5: app.ts Store 简化

**移除**:
- `sidebarCollapsed` ref → shadcn Sidebar 自带状态管理
- `toggleSidebar()` → 由 SidebarTrigger 处理
- `setSidebarCollapsed()` → 同上
- `setDevice()` → shadcn Sidebar 内置 isMobile 判断

**保留**:
- `device` computed（只读，供其他组件判断设备类型）

## Risks / Trade-offs

- [删除 TagsView 可能影响习惯标签页的用户] → 面包屑 + 侧边栏导航足够，后续可按需恢复
- [菜单分组模型增加复杂度] → 当前菜单结构简单，AppNavMain 支持但不强制分组
- [icon 折叠模式占用水平空间] → 48-64px 可接受，比 offcanvas 更易用