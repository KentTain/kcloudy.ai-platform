# CLAUDE.md

本文件为 Claude Code 在前端应用目录工作时提供指导。

## 目录定位

`web/` 目录包含多种前端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 | 详细文档 |
|--------|------|------|------|----------|
| Vue | TypeScript 5.x | Vue 3.5 + Vite 6.x | ✅ 可用 | [vue/CLAUDE.md](vue/CLAUDE.md) |
| React | TypeScript 5.x | React 19 + Vite 6.x | 🚧 规划中 | - |

## 项目结构

```text
web/
└── {技术栈}/                  # 技术栈目录
    ├── src/                    # 源码目录
    │   ├── components/         # 技术栈通用组件
    │   ├── composables/        # Vue 组合式函数 (仅 Vue)
    │   ├── hooks/              # React Hooks (仅 React)
    │   ├── framework/          # 框架层 (路由/状态/布局/权限)
    │   └── {模块}/             # 业务模块
    │       └── components/     # 模块级通用组件
    │
    └── tests/                  # 测试目录
        └── {模块}/             # 模块测试
```

## 架构规则

| 规则 | 说明 |
|------|------|
| 分层架构 | Screens → Components → Stores → API |
| 模块隔离 | 每个业务模块独立路由和状态 |
| 依赖边界 | 业务模块可依赖 framework，反向禁止 |

## UI 组件技术选型

所有前端技术栈采用统一的 UI 组件技术方案：

| 技术层 | Vue | React | 说明 |
|--------|-----|-------|------|
| 组件库 | shadcn-vue | shadcn/ui | 基于 Radix + Tailwind 的组件集 |
| 无样式原语 | Radix Vue | Radix UI | 提供可访问性的底层原语 |
| 样式方案 | Tailwind CSS v4 | Tailwind CSS v4 | 原子化 CSS |

### 组件组织结构

| 层级 | 目录 | 说明 |
|------|------|------|
| UI 基础组件 | `web/{技术栈}/src/components/ui/` | shadcn 组件存放位置 |
| 技术栈通用组件 | `web/{技术栈}/src/components/` | 跨模块共享，业务无关 |
| 模块级通用组件 | `web/{技术栈}/src/{模块}/components/` | 模块专用，与模块功能耦合 |

### 组件命名规范

| 层级 | 前缀 | 示例 | 说明 |
|------|------|------|------|
| UI 基础组件 | 无前缀 | Button, Dialog | shadcn 组件，直接使用原名 |
| 技术栈通用组件 | Common | CommonButton | 跨模块共享的基础组件 |
| 模块级通用组件 | {模块} | DemoDatasetCard | 模块专用组件，带模块前缀 |
| 框架级组件 | App | AppForm | 与框架功能耦合的组件 |

## 环境要求

- Node.js 22+
- pnpm 10+
