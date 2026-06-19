# 前端应用

本目录包含多种前端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 目录结构

```text
web/
└── {技术栈}/                     # 技术栈目录
    ├── src/                      # 源码目录
    │   ├── components/           # 通用组件
    │   │   └── ui/               # UI 基础组件
    │   ├── framework/            # 框架层（路由/状态/布局/权限）
    │   └── {模块}/               # 业务模块
    │       ├── api/              # API 客户端
    │       ├── components/       # 模块专用组件
    │       ├── pages/            # 页面组件
    │       ├── router/           # 路由配置
    │       └── stores/           # 状态管理
    │
    └── tests/                    # 测试目录
        └── {模块}/               # 模块测试
```

## 技术栈概览

| 技术栈 | 语言 | 框架 | 状态 | 文档 |
|--------|------|------|------|------|
| Vue | TypeScript 5.x | Vue 3.5 + Vite 6.x | ✅ 可用 | [README](vue/README.md) |
| React | TypeScript 5.x | React 19 + Vite 6.x | 🚧 规划中 | - |

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
| shadcn | UI 组件库 |
| Radix | 无样式原语（可访问性） |
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

node --version  # v22.x.x
```

**pnpm 10.x**

```bash
npm install -g pnpm
pnpm --version  # 10.x.x
```

### 2. 启动后端服务

前端需要后端 API 支持，请先启动后端服务：

```bash
# Python 后端（推荐）
cd server/python
uv sync
uv run python manage.py runserver
# http://localhost:8000
```

### 3. 启动前端

**Vue 前端**

```bash
cd web/vue
pnpm install
pnpm dev
# http://localhost:5173
```

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
