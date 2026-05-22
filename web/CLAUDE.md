# CLAUDE.md

本文件为 Claude Code 在前端应用目录工作时提供指导。

## 目录概述

`web/` 目录包含多种前端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范，提供可对比、可学习的多技术栈参考。

**核心目标：** 提供功能等价的多技术栈前端实现，便于技术选型对比和团队学习。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 |
|--------|------|------|------|
| Vue | TypeScript 5.x | Vue 3.5 + Vite 6.x | ✅ 可用 |
| React | TypeScript 5.x | React 19 + Vite 6.x | 🚧 规划中 |

**各技术栈详细文档：**

- Vue: [vue/CLAUDE.md](vue/CLAUDE.md)
- React: [react/CLAUDE.md](react/CLAUDE.md) (规划中)

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

## 组件组织结构

前端 PC 端采用两层组件组织结构：

| 层级 | 目录 | 说明 |
|------|------|------|
| 技术栈通用组件 | `web/{技术栈}/src/components/` | 跨模块共享，业务无关 |
| 模块级通用组件 | `web/{技术栈}/src/{模块}/components/` | 模块专用，与模块功能耦合 |

### 组件命名规范

| 层级 | 前缀 | 示例 | 说明 |
|------|------|------|------|
| 技术栈通用组件 | `Common` | `CommonButton` | 跨模块共享的基础组件 |
| 模块级通用组件 | `{模块}` | `DemoDatasetCard` | 模块专用组件，带模块前缀 |
| 框架级组件 | `App` | `AppForm` | 与框架功能耦合的组件 |

## 环境要求

- Node.js 22+
- pnpm 10+

## License

Copyright © 2025 Moles. All Rights Reserved.
