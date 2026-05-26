# CLAUDE.md

本文件为 Claude Code 在 Vue 前端项目中工作时提供指导。

## 项目概述

Vue 前端使用 Vue 3 + TypeScript + Vite 构建，提供 AI 助手平台演示界面。项目采用模块化结构，支持功能模块的独立开发。

**核心技术栈：**

- 框架：Vue 3.5, TypeScript 5.8
- 构建：Vite 6.x
- 路由：Vue Router 4.x
- 状态管理：Pinia 3.x
- UI 组件库：shadcn-vue
- 无样式原语：Radix Vue
- 样式：Tailwind CSS v4
- 代码质量：Biome
- 测试：Vitest, @vue/test-utils

## UI 组件技术

### shadcn-vue

shadcn-vue 是基于 Radix Vue + Tailwind CSS 的组件库。与传统组件库不同，shadcn-vue 的组件代码会被复制到项目中，而非作为依赖安装。

```bash
# 添加组件
npx shadcn-vue@latest add button
npx shadcn-vue@latest add dialog
npx shadcn-vue@latest add form
```

组件代码将被复制到 `src/components/ui/` 目录，可完全定制。

### Radix Vue

Radix Vue 提供无样式的可访问性原语组件，是 shadcn-vue 的底层依赖。

```typescript
// 当 shadcn-vue 没有需要的组件时，可直接使用 Radix Vue
import { DropdownMenu } from 'radix-vue'
```

### 技术关系

```
┌─────────────────────────────────────────────────────────────┐
│  shadcn-vue                                                 │
│  ├── Button, Dialog, Form, Table...                         │
│  ├── 基于 Radix Vue 原语                                    │
│  └── Tailwind CSS 样式                                      │
├─────────────────────────────────────────────────────────────┤
│  Radix Vue                                                  │
│  ├── 提供可访问性原语                                        │
│  └── 无样式，由 shadcn-vue 封装                              │
├─────────────────────────────────────────────────────────────┤
│  Tailwind CSS v4                                            │
│  └── 原子化 CSS，提供样式基础                                │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```text
web/vue/
├── src/                       # 源码目录
│   ├── components/            # 通用组件
│   │   └── ui/                # shadcn-vue 组件
│   ├── composables/           # 组合式函数 (Vue)
│   ├── framework/             # Framework 前端UI框架模块
│   ├── tenant/                # Tenant 租户管理模块
│   ├── iam/                   # IAM 身份认证与权限模块
│   ├── demo/                  # Demo 业务模块
│   ├── App.vue                # 根组件
│   └── main.ts                # 应用入口
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
|------|------|----------|
| components/ui | shadcn-vue UI 组件 | 由 shadcn-vue CLI 管理 |
| framework | 基础设施：前端UI框架、路由、状态管理 | [src/framework/CLAUDE.md](src/framework/CLAUDE.md) |
| tenant | 租户管理模块：租户创建、切换、配置 | [src/tenant/CLAUDE.md](src/tenant/CLAUDE.md) |
| iam | 身份认证与权限模块：用户、角色、权限管理 | [src/iam/CLAUDE.md](src/iam/CLAUDE.md) |
| demo | 业务演示模块：健康检查、知识库管理 | [src/demo/CLAUDE.md](src/demo/CLAUDE.md) |

## 开发命令

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 指定端口启动
pnpm dev --port 3000

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
- **组件语法**：`<script setup lang="ts">`

## 详细文档

- **开发指南**：[src/CLAUDE.md](src/CLAUDE.md)
- **测试指南**：[tests/CLAUDE.md](tests/CLAUDE.md)

## 环境要求

- Node.js 22+
- pnpm 10+

## License

Copyright © 2025 Moles. All Rights Reserved.
