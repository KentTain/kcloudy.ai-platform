# header-shortcuts Specification

## Purpose
TBD - created by archiving change enhance-admin-shell-ui. Update Purpose after archive.
## Requirements
### Requirement: Header horizontal navigation
Header SHALL 在 SidebarTrigger 和面包屑之后显示 NavigationMenu 水平导航，提供核心页面快捷入口。

#### Scenario: Display primary navigation items
- **WHEN** 用户在 `lg` 及以上屏幕宽度访问系统
- **THEN** Header 显示 NavigationMenu，包含"首页"、"知识库"等核心页面链接

#### Scenario: Hide navigation on mobile
- **WHEN** 用户在 `md` 及以下屏幕宽度访问系统
- **THEN** Header 隐藏 NavigationMenu 水平导航

#### Scenario: Navigate via horizontal nav
- **WHEN** 用户点击 NavigationMenu 中的"知识库"链接
- **THEN** 系统跳转至 `/datasets` 页面

### Requirement: Header quick action buttons
Header SHALL 在搜索区域旁提供快捷操作按钮（待办、通知等预留入口）。

#### Scenario: Display quick action buttons
- **WHEN** 用户已登录
- **THEN** Header 搜索区域右侧显示待办和通知的图标按钮

#### Scenario: Navigate via quick action
- **WHEN** 用户点击通知图标按钮
- **THEN** 系统跳转至预留的通知页面路由

### Requirement: Header search trigger
Header SHALL 在右侧区域提供搜索输入区域，点击后打开命令面板。

#### Scenario: Click search to open command palette
- **WHEN** 用户点击 Header 搜索区域
- **THEN** 系统打开全局命令面板

