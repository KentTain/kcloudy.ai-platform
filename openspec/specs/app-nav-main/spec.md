# App Nav Main 规范

## Purpose

定义分组侧边栏菜单组件，支持分组标题、子菜单展开/折叠和路由导航。

## Requirements

### Requirement: AppNavMain 分组菜单组件

系统 SHALL 提供 AppNavMain 组件用于渲染分组侧边栏菜单。

#### Scenario: 渲染分组菜单

- **WHEN** 使用 AppNavMain 组件并传入 items 数组
- **THEN** 系统 SHALL 为每个分组渲染：
  - SidebarGroup 容器
  - SidebarGroupLabel（如果分组有 title）
  - SidebarMenu 包含菜单项

#### Scenario: 渲染菜单项

- **WHEN** 菜单项为 AppNavItem 类型（无子菜单）
- **THEN** 系统 SHALL 渲染：
  - SidebarMenuItem
  - SidebarMenuButton（支持 icon、title、isActive、tooltip）
  - 点击时导航到 url

#### Scenario: 渲染子菜单

- **WHEN** 菜单项为 AppNavSub 类型（有子菜单）
- **THEN** 系统 SHALL 渲染：
  - Collapsible 容器
  - SidebarMenuButton 显示 icon 和 title
  - 展开时显示 SidebarMenuSub 子菜单项
  - ChevronRight 箭头指示展开状态

#### Scenario: 选中状态判断

- **WHEN** 当前路由路径匹配菜单项 url
- **THEN** 系统 SHALL 将该菜单项的 isActive 设为 true

#### Scenario: 导航交互

- **WHEN** 用户点击菜单项
- **THEN** 系统 SHALL 使用 router.push 导航到对应 url