# Demo Module 规格说明

## MODIFIED Requirements

### Requirement: Demo 模块布局迁移

Demo 模块页面 SHALL 迁移至 AdminLayout 布局框架。

#### Scenario: 使用 AdminLayout

- **WHEN** Demo 模块页面加载
- **THEN** 系统 SHALL 使用 AdminLayout 作为壳布局

#### Scenario: 侧边栏菜单

- **WHEN** Demo 模块菜单渲染
- **THEN** 系统 SHALL 在 AppSidebar 中显示：
  - 健康检查菜单项
  - 知识库管理菜单项

### Requirement: Demo 模块样式迁移

Demo 模块组件 SHALL 使用设计令牌替代硬编码颜色。

#### Scenario: Button 组件迁移

- **WHEN** Demo 模块使用 Button 组件
- **THEN** 系统 SHALL 使用语义化 class（`bg-primary`、`text-primary` 等）

#### Scenario: Card 组件迁移

- **WHEN** Demo 模块使用 Card 组件
- **THEN** 系统 SHALL 使用设计令牌定义的样式

### Requirement: Demo 模块路由配置

Demo 模块路由 SHALL 使用新路由配置格式。

#### Scenario: 路由元信息

- **WHEN** 定义 Demo 模块路由
- **THEN** 系统 SHALL 包含以下 meta 信息：
  - `title` - 页面标题
  - `icon` - 菜单图标
  - `requiresAuth` - 是否需要登录

#### Scenario: 路由懒加载

- **WHEN** 定义 Demo 模块路由
- **THEN** 系统 SHALL 使用动态导入实现懒加载
