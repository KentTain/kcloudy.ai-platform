# 前端应用

本目录包含多种前端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 目录结构

```text
web/
├── vue/                      # Vue 前端 ✅
└── react/                    # React 前端 🚧
```

## 技术栈概览

| 技术栈 | 语言 | 框架 | 状态 | 文档 |
|--------|------|------|------|------|
| Vue | TypeScript 5.x | Vue 3.5 + Vite 6.x | ✅ 可用 | [README](vue/README.md) |
| React | TypeScript 5.x | React 19 + Vite 6.x | 🚧 规划中 | - |

## 技术栈对比

### 完整技术选型

| 类别 | Vue | React | 说明 |
|------|-----|-------|------|
| **核心框架** | Vue 3.5 | React 19 | 响应式 vs 重新渲染 |
| **构建工具** | Vite 6.x | Vite 6.x | 相同 |
| **语言** | TypeScript 5.x | TypeScript 5.x | 相同 |
| **路由** | Vue Router 4.x | TanStack Router | 都支持类型安全路由 |
| **状态管理** | Pinia 3.x | Zustand | 相似的 store 模式 |
| **样式** | Tailwind CSS v4 | Tailwind CSS v4 | 相同 |
| **HTTP 客户端** | Axios | Axios | 相同 |
| **测试框架** | Vitest | Vitest | 相同 |
| **组件测试** | @vue/test-utils | @testing-library/react | 框架配套工具 |
| **Lint/Format** | Biome | Biome | 相同 |

### 状态管理对比

| 特性 | Vue (Pinia) | React (Zustand) |
|------|-------------|-----------------|
| Store 定义 | `defineStore()` | `create()` |
| 状态访问 | `storeToRefs()` | 直接解构 |
| Actions | Store 内定义 | Store 内定义 |
| TypeScript | 自动推断 | 需要类型标注 |
| DevTools | Vue DevTools 集成 | 独立 DevTools |
| 学习曲线 | 平缓 | 简单 |

### 路由对比

| 特性 | Vue (Vue Router) | React (TanStack Router) |
|------|------------------|------------------------|
| 配置方式 | 配置对象 / 文件路由 | 文件路由优先 |
| 类型安全 | 需手动标注 | 自动类型推断 |
| 数据加载 | 导航守卫 | Loader 模式 |
| 懒加载 | `() => import()` | `lazy()` |

### 项目结构差异

| 目录 | Vue | React | 说明 |
|------|-----|-------|------|
| 复用逻辑 | `src/composables/` | `src/hooks/` | 命名约定不同 |
| 组件文件 | `*.vue` (SFC) | `*.tsx` (函数组件) | 文件格式不同 |
| 根组件 | `App.vue` | `App.tsx` | 文件格式不同 |

## 统一架构

所有技术栈采用统一的前端架构和基础设施：

### 架构分层

| 层级 | 职责 |
|------|------|
| Pages | 页面组件，路由对应的视图 |
| Components | 可复用的 UI 组件 |
| Stores | 全局状态管理 |
| API | HTTP 请求封装 |
| Composables | 可复用的组合式函数 |

### 基础设施

| 组件 | 用途 |
|------|------|
| Vite 6.x | 开发服务器、构建工具 |
| TypeScript 5.x | 类型系统 |
| Tailwind CSS v4 | 样式框架 |
| Axios | HTTP 客户端 |
| Vitest | 测试框架 |
| Biome | Lint + Format |

### 统一 API

所有技术栈通过 Vite proxy 转发请求到后端：

```
/api/*    → http://127.0.0.1:8000/api/*
/health/* → http://127.0.0.1:8000/health/*
```

## 快速开始

### 1. 准备环境

**Node.js 22+**

```bash
# Windows (scoop)
scoop install nodejs-lts

# macOS
brew install node@22

# 验证版本
node --version  # v22.x.x
```

**pnpm 10.x**

```bash
# 安装 pnpm
npm install -g pnpm

# 验证版本
pnpm --version  # 10.x.x
```

### 2. 启动后端服务

前端需要后端 API 支持，请先启动后端服务：

```bash
# Python 后端（推荐）
cd server/python
uv sync
uv run runserver
# 后端运行在 http://localhost:8000

# 或 Rust 后端
cd server/rust
cargo run
# 后端运行在 http://localhost:8000
```

### 3. 启动前端

**Vue 前端**

```bash
cd web/vue
pnpm install
pnpm dev
# 访问 http://localhost:5173
```

详细说明请参阅各技术栈的 README 文档。

## 开发指南

各技术栈的详细开发指南请参阅对应的 CLAUDE.md 文档：

- [整体开发指南](CLAUDE.md)
- [Vue 开发指南](vue/CLAUDE.md)
- [React 开发指南](react/CLAUDE.md) (规划中)

## 环境要求

| 技术栈 | 语言版本 | 包管理器 |
|--------|----------|----------|
| Vue | Node.js 22+ | pnpm 10.x |
| React | Node.js 22+ | pnpm 10.x |

## License

Copyright © 2025 Moles. All Rights Reserved.
