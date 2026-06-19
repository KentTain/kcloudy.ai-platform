## MODIFIED Requirements

### Requirement: AdminLayout 壳布局

系统 SHALL 提供 AdminLayout 组件作为后台管理系统的整体布局容器，使用 shadcn Sidebar 组件体系。

#### Scenario: 布局结构

- **WHEN** 使用 AdminLayout 组件
- **THEN** 系统 SHALL 包含以下子组件：
  - SidebarProvider - Sidebar 状态提供者
  - Sidebar - 侧边栏（collapsible="icon"）
  - SidebarInset - 内容区容器
  - Header - 顶部导航（在 SidebarInset 内）
  - AppMain - 页面内容区

#### Scenario: 响应式布局

- **WHEN** 浏览器宽度小于 md 断点
- **THEN** 系统 SHALL 自动将 Sidebar 切换为 Sheet 模式（由 shadcn Sidebar 内置处理）

#### Scenario: 容器高度

- **WHEN** AdminLayout 渲染完成
- **THEN** 系统 SHALL 设置容器高度为 `h-svh overflow-hidden`（100svh，超出隐藏）

### Requirement: Sidebar 侧边栏

系统 SHALL 提供基于 shadcn Sidebar 的可折叠侧边栏组件。

#### Scenario: icon 折叠模式

- **WHEN** 侧边栏处于折叠状态
- **THEN** 系统 SHALL 显示：
  - 宽度自动收缩为 `--sidebar-width-icon`（约 48-56px）
  - 仅显示菜单图标
  - 悬停时显示 Tooltip 提示菜单名称

#### Scenario: 展开状态

- **WHEN** 侧边栏处于展开状态
- **THEN** 系统 SHALL 显示：
  - 宽度 `--sidebar-width`（约 240px）
  - Logo 区域
  - 分组菜单（AppNavMain）
  - 用户信息区域

#### Scenario: 菜单项选中态

- **WHEN** 菜单项被选中
- **THEN** 系统 SHALL 显示：
  - SidebarMenuButton 的 isActive 为 true
  - 默认选中样式（背景高亮）

#### Scenario: SidebarTrigger 控制

- **WHEN** 用户点击 SidebarTrigger
- **THEN** 系统 SHALL 切换侧边栏展开/折叠状态

### Requirement: Header 顶部导航

系统 SHALL 提供 56px（3.5rem）高度的顶部导航组件，位于 SidebarInset 内。

#### Scenario: 默认功能

- **WHEN** 顶部导航加载完成
- **THEN** 系统 SHALL 显示：
  - 左侧：SidebarTrigger、Separator、Breadcrumb

#### Scenario: 面包屑导航

- **WHEN** 页面路由匹配到 meta.title
- **THEN** 系统 SHALL 在 Breadcrumb 中显示路径层级

### Requirement: SidebarFooter 用户信息

系统 SHALL 在 SidebarFooter 中提供用户信息区域和退出登录功能。

#### Scenario: 用户信息显示

- **WHEN** 侧边栏处于展开状态
- **THEN** 系统 SHALL 显示：
  - 用户头像（AvatarFallback）
  - 用户昵称
  - 用户邮箱

#### Scenario: 退出登录

- **WHEN** 用户点击 SidebarFooter 中的用户菜单
- **THEN** 系统 SHALL 显示 DropdownMenu：
  - 退出登录选项

## REMOVED Requirements

### Requirement: AppTagsView 标签页

**Reason**: 现代工作台风格不需要传统后台标签页导航，面包屑 + 侧边栏已足够。删除后代码更简洁。

**Migration**: 无需迁移，TagsView 功能直接移除。用户通过面包屑和侧边栏导航。
