# Admin UI Framework 实现方案

## Why

当前 `web/vue` 项目仅有基础的侧栏 + 内容区布局，缺少完整的后台管理系统框架。设计规范文档 `docs/前端PC端设计规范及框架设计探索.md` 已明确浅色专业后台的设计方向（蔚蓝主色 + 橙红辅色），但现有实现尚未对齐设计令牌，且 UI 组件库覆盖不足，无法支撑业务模块开发。

本项目旨在建立统一的前端 UI 框架，为后续业务模块提供一致的视觉语言、布局架构和权限控制能力。

## What Changes

### 新增能力

- **设计令牌系统**：基于 Tailwind CSS v4 `@theme`，定义蔚蓝主色、橙红辅色、语义色、字体、圆角等设计令牌
- **AdminLayout 布局组件**：侧边栏（可折叠）+ 顶部导航 + TagsView + 内容区的完整布局
- **UI 组件库扩展**：Input、Select、Table、Form 等高频后台组件
- **权限控制系统**：动态路由注册 + `v-permission` 指令 + 接口权限拦截

### 修改内容

- **BREAKING** 现有 `AppButton`、`AppCard`、`AppLoading`、`AppModal` 组件改用语义化设计令牌
- **BREAKING** `MainLayout.vue` 重构为 `AdminLayout.vue`，增加 Navbar 和 TagsView
- 现有 Demo 模块页面迁移至新布局框架

## Capabilities

### New Capabilities

- `design-tokens`: 设计令牌系统（颜色、字体、间距、圆角），基于 Tailwind CSS v4 `@theme` 实现
- `admin-layout`: AdminLayout 布局组件（AppSidebar、AppNavbar、AppTagsView、AppMain）
- `ui-components`: UI 组件库（Button、Input、Select、Table、Form、Modal、Card 等）
- `permission-system`: 权限控制系统（动态路由、v-permission 指令、接口拦截）

### Modified Capabilities

- `demo-module`: Demo 模块页面迁移至新布局框架，使用设计令牌

## Impact

### 受影响代码

| 路径 | 影响类型 |
|------|----------|
| `web/vue/src/framework/styles/` | 新增设计令牌文件 |
| `web/vue/src/framework/layouts/` | 新增 AdminLayout 组件 |
| `web/vue/src/framework/components/ui/` | 扩展 UI 组件库 |
| `web/vue/src/framework/router/` | 增加动态路由和权限守卫 |
| `web/vue/src/framework/stores/` | 新增 permission store |
| `web/vue/src/demo/` | 迁移至新布局框架 |

### API 依赖

- 需要后端提供菜单权限 API（`/admin/v1/menus`）
- 需要后端提供用户权限码 API（`/admin/v1/permissions`）

### 兼容性考虑

- 设计令牌采用 CSS 变量实现，支持 `data-theme` 扩展暗色主题
- UI 组件基于 Tailwind CSS v4，不引入 Element Plus，避免双套视觉语言
- 权限系统预留后端集成接口，当前可使用 mock 数据
