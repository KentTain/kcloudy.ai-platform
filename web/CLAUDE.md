# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在前端应用目录工作时提供指导。

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

## 技术选型

| 技术栈 | 核心技术 | 详细文档 |
|--------|----------|----------|
| Vue | Vue 3.5 + Vite + Pinia + Vue Router + Tailwind CSS | [vue/CLAUDE.md](vue/CLAUDE.md) |
| React | React 19 + Vite + Zustand + TanStack Router + Tailwind CSS | [react/CLAUDE.md](react/CLAUDE.md) (规划中) |

## 项目结构

所有技术栈采用统一的前端架构：

```text
web/
└── {技术栈}/
    ├── src/
    │   ├── api/              # API 客户端
    │   ├── components/       # 通用组件
    │   │   └── ui/           # UI 基础组件
    │   ├── composables/      # 组合式函数 (Vue)
    │   ├── hooks/            # React Hooks (React)
    │   ├── layouts/          # 布局组件
    │   ├── pages/            # 页面组件
    │   ├── router/           # 路由配置
    │   ├── stores/           # 状态管理
    │   ├── styles/           # 全局样式
    │   ├── types/            # TypeScript 类型定义
    │   ├── App.vue/App.tsx   # 根组件
    │   └── main.ts           # 应用入口
    ├── tests/                # 测试文件
    ├── biome.jsonc           # Biome 配置
    ├── vite.config.ts        # Vite 配置
    └── vitest.config.ts      # Vitest 配置
```

## 分层架构

| 层级 | 职责 |
|------|------|
| Pages | 页面组件，路由对应的视图 |
| Components | 可复用的 UI 组件 |
| Stores | 全局状态管理 |
| API | HTTP 请求封装 |
| Composables/Hooks | 可复用逻辑 |

## 统一基础设施

| 组件 | 用途 |
|------|------|
| Vite 6.x | 开发服务器、构建工具 |
| TypeScript 5.x | 类型系统 |
| Tailwind CSS v4 | 样式框架 |
| Axios | HTTP 客户端 |
| Vitest | 测试框架 |
| Biome | Lint + Format |

## API 规范

### 代理配置

开发环境通过 Vite proxy 转发 API 请求到后端 `http://127.0.0.1:8000`：

- `/api/*` → 后端 API
- `/health` → 健康检查

### RESTful 规范

- URL 设计：资源导向，小写连字符分隔
- HTTP 方法：GET 查询、POST 创建、PUT 更新、DELETE 删除
- 响应格式：统一 JSON 结构，包含 `code`、`message`、`data` 字段

## 开发规范

- 遵循各框架的社区规范和最佳实践
- 统一使用 TypeScript 编写代码
- 使用 Biome 进行 Lint 和 Format
- 统一使用 Conventional Commits 提交规范

## 环境要求

- Node.js 22+
- pnpm 10+

## License

Copyright © 2025 Moles. All Rights Reserved.
