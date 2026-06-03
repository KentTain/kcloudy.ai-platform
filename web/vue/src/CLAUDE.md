# Vue 前端开发指南

本文件为 Claude Code 在 Vue 前端源码目录中工作时提供指导。

## 目录定位

`src/` 按顶级模块组织源码。模块是 `src/{module}/`，功能是模块内的子域；不要把功能域提升为新的顶级目录。

## 顶级模块

| 模块 | 定位 | 详细文档 |
|------|------|----------|
| framework | 基础设施：UI框架、路由、状态管理 | [framework/CLAUDE.md](framework/CLAUDE.md) |
| tenant | 租户管理模块 | [tenant/CLAUDE.md](tenant/CLAUDE.md) |
| iam | 身份认证与权限模块 | [iam/CLAUDE.md](iam/CLAUDE.md) |
| demo | 业务演示模块 | [demo/CLAUDE.md](demo/CLAUDE.md) |
| components | 通用组件（跨模块共享） | - |
| composables | 组合式函数 | - |

## 依赖边界

```
demo / iam / tenant ──▶ framework
framework ──X──▶ demo / iam / tenant
```

- 业务模块可以依赖 `framework`
- `framework` 禁止依赖业务模块
- 跨模块通信通过 Pinia Store、EventBus 或 API 调用

## 模块结构规范

每个业务模块必须包含：

```
src/{module}/
├── index.ts              # 模块入口，导出 ModuleDescriptor
├── router/
│   └── index.ts          # 模块路由配置（必需）
├── api/                  # API 函数
├── types/                # TypeScript 类型定义
├── pages/                # 页面组件
├── components/           # 模块专用组件
└── stores/               # Pinia 状态管理
```

## 组件层级规范

| 层级 | 目录 | 前缀 | 说明 |
|------|------|------|------|
| UI 基础组件 | `src/components/ui/` | 无前缀 | shadcn 组件 |
| 技术栈通用组件 | `src/components/` | Common | 跨模块共享 |
| 模块级组件 | `{模块}/components/` | {模块} | 模块专用 |
| 框架级组件 | `framework/components/` | App | 框架功能耦合 |

## 开发约束

- 新模块放在 `src/{module}/`
- 必须在 `index.ts` 导出 `ModuleDescriptor`
- 必须在 `router/index.ts` 定义模块路由
- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore` 和 Composition API
- 页面组件使用 `AppPage` 组件作为页面骨架
