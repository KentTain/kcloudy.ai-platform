# CLAUDE.md

本文件为 Claude Code 在 React 前端项目中工作时提供指导。

## 项目概述

React 前端使用 React 19 + TypeScript + Vite 构建，提供 AI 助手平台演示界面。项目采用模块化结构，支持功能模块的独立开发。

**核心技术栈：**

- 框架：React 19, TypeScript 5.8
- 构建：Vite 6.x
- 路由：React Router 7.x
- 状态管理：Zustand 5.x
- UI 组件库：shadcn/ui
- 无样式原语：Radix UI
- 样式：Tailwind CSS v4
- 代码质量：Biome
- 测试：Vitest, @testing-library/react

## UI 组件技术

### shadcn/ui

shadcn/ui 是基于 Radix UI + Tailwind CSS 的组件库。与传统组件库不同，shadcn/ui 的组件代码会被复制到项目中，而非作为依赖安装。

```bash
# 添加组件
npx shadcn@latest add button
npx shadcn@latest add dialog
npx shadcn@latest add form
```

组件代码将被复制到 `src/components/ui/` 目录，可完全定制。

### Radix UI

Radix UI 提供无样式的可访问性原语组件，是 shadcn/ui 的底层依赖。

```typescript
// 当 shadcn/ui 没有需要的组件时，可直接使用 Radix UI
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
```

### 技术关系

```
┌─────────────────────────────────────────────────────────────┐
│  shadcn/ui                                                  │
│  ├── Button, Dialog, Form, Table...                         │
│  ├── 基于 Radix UI 原语                                     │
│  └── Tailwind CSS 样式                                      │
├─────────────────────────────────────────────────────────────┤
│  Radix UI                                                   │
│  ├── 提供可访问性原语                                        │
│  └── 无样式，由 shadcn/ui 封装                               │
├─────────────────────────────────────────────────────────────┤
│  Tailwind CSS v4                                            │
│  └── 原子化 CSS，提供样式基础                                │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```text
web/react/
├── src/                       # 源码目录
│   ├── components/            # 通用组件
│   │   └── ui/                # shadcn/ui 组件
│   ├── hooks/                 # React Hooks
│   ├── framework/             # Framework 前端UI框架模块
│   ├── demo/                  # Demo 业务模块
│   ├── App.tsx                # 根组件
│   └── main.tsx               # 应用入口
├── tests/                     # 测试目录
│   ├── demo/                  # Demo 模块测试
│   └── framework/             # Framework 模块测试
├── public/                    # 静态文件
├── biome.jsonc                # Biome 配置
├── vite.config.ts             # Vite 配置
├── vitest.config.ts           # Vitest 测试配置
├── tsconfig.json              # TypeScript 配置
├── tsconfig.vitest.json       # Vitest TypeScript 配置
└── package.json               # 项目配置
```

## 功能模块

| 模块 | 说明 | 详细文档 |
| --- | --- | --- |
| components/ui | shadcn/ui UI 组件 | 由 shadcn CLI 管理 |
| components | 通用组件 | [src/components/CLAUDE.md](src/components/CLAUDE.md) |
| hooks | React Hooks | [src/hooks/CLAUDE.md](src/hooks/CLAUDE.md) |
| framework | 基础设施：前端UI框架、路由、状态管理 | [src/framework/CLAUDE.md](src/framework/CLAUDE.md) |
| demo | 业务演示模块：健康检查、知识库管理 | [src/demo/CLAUDE.md](src/demo/CLAUDE.md) |

## 开发命令

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 指定端口启动
pnpm dev --port 3001

# 生产构建
pnpm build

# 类型检查
pnpm type-check

# 代码检查
pnpm check           # Biome lint + format 检查
pnpm check:fix       # 自动修复

# 测试
pnpm test:unit
pnpm test:unit -- --run
pnpm test:unit -- --coverage
```

## 配置管理

开发环境通过 Vite proxy 转发 API 请求到后端 `http://127.0.0.1:8000`：

- `/api/*` → 后端 API
- `/health` → 健康检查

## 代码质量标准

- **Linter/格式化**：Biome
- **行宽**：100 字符
- **TypeScript 版本**：5.8
- **组件语法**：React 函数组件 + TypeScript

## 详细文档

- **开发指南**：[src/CLAUDE.md](src/CLAUDE.md)
- **测试指南**：[tests/CLAUDE.md](tests/CLAUDE.md)

## 环境要求

- Node.js 22+
- pnpm 10+

## License

Copyright © 2025 Moles. All Rights Reserved.
