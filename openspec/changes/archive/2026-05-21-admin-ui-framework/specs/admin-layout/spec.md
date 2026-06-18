# Admin Layout 规格说明

## ADDED Requirements

### Requirement: AdminLayout 壳布局

系统 SHALL 提供 AdminLayout 组件作为后台管理系统的整体布局容器。

#### Scenario: 布局结构

- **WHEN** 使用 AdminLayout 组件
- **THEN** 系统 SHALL 包含以下子组件：
  - AppSidebar - 侧边栏
  - AppNavbar - 顶部导航
  - AppTagsView - 标签页
  - AppMain - 内容区

#### Scenario: 响应式布局

- **WHEN** 浏览器宽度小于 768px
- **THEN** 系统 SHALL 自动折叠侧边栏

### Requirement: AppSidebar 侧边栏

系统 SHALL 提供可折叠的侧边栏组件。

#### Scenario: 展开状态

- **WHEN** 侧边栏处于展开状态
- **THEN** 系统 SHALL 显示：
  - 宽度 240px
  - 白色背景 `#FFFFFF`
  - 右边框 `#E5E7EB`
  - 菜单图标 + 文字

#### Scenario: 折叠状态

- **WHEN** 侧边栏处于折叠状态
- **THEN** 系统 SHALL 显示：
  - 宽度 64px
  - 仅菜单图标
  - 悬停时显示 Tooltip 提示菜单名称

#### Scenario: 菜单项选中态

- **WHEN** 菜单项被选中
- **THEN** 系统 SHALL 显示：
  - 文字/图标颜色 `primary`
  - 背景 `primary-subtle`
  - 左侧 3px `primary` 指示条

### Requirement: AppNavbar 顶部导航

系统 SHALL 提供 60px 高度的顶部导航组件。

#### Scenario: 默认功能

- **WHEN** 顶部导航加载完成
- **THEN** 系统 SHALL 显示：
  - 左侧：折叠按钮、面包屑
  - 右侧：全屏、消息、用户菜单

#### Scenario: 折叠按钮交互

- **WHEN** 用户点击折叠按钮
- **THEN** 系统 SHALL 切换侧边栏展开/折叠状态

#### Scenario: 用户菜单

- **WHEN** 用户点击用户头像
- **THEN** 系统 SHALL 显示下拉菜单：
  - 个人中心
  - 退出登录

### Requirement: AppTagsView 标签页

系统 SHALL 提供页面标签页组件，支持多页面切换。

#### Scenario: 标签页显示

- **WHEN** 用户访问页面
- **THEN** 系统 SHALL 在 TagsView 区域添加对应标签

#### Scenario: 选中标签样式

- **WHEN** 标签被选中
- **THEN** 系统 SHALL 显示：
  - 文字颜色 `primary`
  - 底部 2px `primary` 边框

#### Scenario: 未选中标签样式

- **WHEN** 标签未被选中
- **THEN** 系统 SHALL 显示：
  - 文字颜色 `text-muted`
  - 无底部边框

#### Scenario: 关闭标签

- **WHEN** 用户点击标签关闭按钮
- **THEN** 系统 SHALL 关闭该标签并切换到相邻标签

### Requirement: AppMain 内容区

系统 SHALL 提供内容区组件用于渲染页面内容。

#### Scenario: 内容区样式

- **WHEN** 内容区渲染完成
- **THEN** 系统 SHALL 显示：
  - 背景 `surface`
  - 内边距 16px
  - 页面切换淡入淡出动效（0.3s）

#### Scenario: 页面加载状态

- **WHEN** 页面正在加载
- **THEN** 系统 SHALL 显示骨架屏代替 Loading 转圈
