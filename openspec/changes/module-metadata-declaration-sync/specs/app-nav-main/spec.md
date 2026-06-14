## ADDED Requirements

### 需求:动态菜单数据源

系统必须支持从外部数据源（API 或 store）动态获取菜单数据。

#### 场景:从 store 获取菜单
- **当** AppNavMain 组件挂载
- **那么** 从 useMenuStore 获取菜单数据

#### 场景:菜单数据为空时显示占位
- **当** 菜单数据为空或加载中
- **那么** 显示加载占位或不渲染菜单区域

### 需求:菜单图标动态渲染

系统必须支持根据图标名称动态渲染图标组件。

#### 场景:渲染已知图标
- **当** 菜单项 icon 为 "Settings"
- **那么** 渲染对应的 Lucide Settings 图标组件

#### 场景:图标名称未知
- **当** 菜单项 icon 为未知名称或为空
- **那么** 渲染默认图标或不渲染图标

## MODIFIED Requirements

### 需求:AppNavMain 分组菜单组件

系统 SHALL 提供 AppNavMain 组件用于渲染分组侧边栏菜单。

#### 场景:渲染分组菜单
- **WHEN** 使用 AppNavMain 组件并传入 items 数组
- **THEN** 系统 SHALL 为每个分组渲染：
  - SidebarGroup 容器
  - SidebarGroupLabel（如果分组有 title）
  - SidebarMenu 包含菜单项

#### 场景:渲染菜单项
- **WHEN** 菜单项为 AppNavItem 类型（无子菜单）
- **THEN** 系统 SHALL 渲染：
  - SidebarMenuItem
  - SidebarMenuButton（支持 icon、title、isActive、tooltip）
  - 点击时导航到 url

#### 场景:渲染子菜单
- **WHEN** 菜单项为 AppNavSub 类型（有子菜单）
- **THEN** 系统 SHALL 渲染：
  - Collapsible 容器
  - SidebarMenuButton 显示 icon 和 title
  - 展开时显示 SidebarMenuSub 子菜单项
  - ChevronRight 箭头指示展开状态

#### 场景:选中状态判断
- **WHEN** 当前路由路径匹配菜单项 url
- **THEN** 系统 SHALL 将该菜单项的 isActive 设为 true

#### 场景:导航交互
- **WHEN** 用户点击菜单项
- **THEN** 系统 SHALL 使用 router.push 导航到对应 url

## REMOVED Requirements

### 需求:硬编码默认菜单
**Reason**: 菜单改为从 API 动态获取，不再需要硬编码
**Migration**: 删除 defaultItems 常量，改为从 useMenuStore 获取菜单数据
