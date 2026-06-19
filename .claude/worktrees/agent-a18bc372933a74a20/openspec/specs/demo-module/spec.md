# Demo Module 规范

## Purpose

定义 Demo 业务演示模块，展示健康检查和知识库管理等功能的页面实现。

## Requirements

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

Demo 模块组件 SHALL 使用 shadcn 组件替代 CommonXxx 封装组件。

#### Scenario: Button 组件迁移

- **WHEN** Demo 模块使用 Button 组件
- **THEN** 系统 SHALL 使用 shadcn Button 替代 CommonButton

#### Scenario: Card 组件迁移

- **WHEN** Demo 模块使用 Card 组件
- **THEN** 系统 SHALL 使用 shadcn Card 替代 CommonCard

#### Scenario: Loading 组件迁移

- **WHEN** Demo 模块需要加载态展示
- **THEN** 系统 SHALL 使用 Skeleton 组件替代 CommonLoading

#### Scenario: 表格组件迁移

- **WHEN** Demo 模块需要列表展示
- **THEN** 系统 SHALL 使用 shadcn Table 组件替代 CommonCard 内的手写列表

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
