# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在前端应用中工作时提供指导。

## 项目概述

InitProject AI 助手平台前端应用（Vue 版本），基于 Vue 3 + TypeScript + Vite 构建，提供知识库管理界面。

**核心技术栈：**

- 框架：Vue 3.5, TypeScript 5.8
- 构建：Vite 6.x
- 路由：Vue Router 4.x
- 状态管理：Pinia 3.x
- 样式：Tailwind CSS v4
- 代码质量：Biome
- 测试：Vitest, @vue/test-utils

## 项目结构

```text
web/vue/
├── src/
│   ├── api/              # API 客户端（Axios 封装）
│   ├── assets/           # 静态资源
│   ├── components/       # 通用组件
│   │   └── ui/           # UI 基础组件（Button, Card, Loading）
│   ├── layouts/          # 布局组件（MainLayout）
│   ├── pages/            # 页面组件
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态管理
│   ├── styles/           # 全局样式
│   ├── types/            # TypeScript 类型定义
│   ├── App.vue           # 根组件
│   └── main.ts           # 应用入口
├── tests/                # 单元测试
│   ├── components/       # 组件测试
│   ├── composables/      # Composable 测试
│   └── stores/           # Store 测试
├── public/               # 静态文件
├── biome.jsonc           # Biome 配置
├── vite.config.ts        # Vite 配置
├── vitest.config.ts      # Vitest 测试配置
├── tsconfig.json         # TypeScript 配置
├── tsconfig.vitest.json  # Vitest TypeScript 配置
└── package.json          # 项目配置
```

## 开发命令

**请从 `web/vue` 目录运行前端命令。Node 版本要求 `>=22.0.0`，pnpm 版本为 `10.x`。**

```bash
pnpm install           # 安装依赖
pnpm dev               # 启动 Vite 开发服务器（端口 5173）
pnpm build             # 生产构建
pnpm preview           # 本地预览生产构建
pnpm type-check        # 使用 vue-tsc 进行类型检查
pnpm check             # 运行 Biome lint + format 检查
pnpm check:fix         # 运行 Biome 检查并自动修复

# 测试
pnpm test:unit         # 运行单元测试
pnpm test:unit -- --run  # 运行一次（不监听）
```

## 架构说明

### API 层

`src/api/` 使用 Axios 封装 HTTP 请求：

- `client.ts` - Axios 实例配置，包含请求/响应拦截器
- `datasets.ts` - 知识库 API 函数
- `health.ts` - 健康检查 API

开发环境通过 Vite proxy 转发 `/api` 到后端 8000 端口。

### 路由

路由配置位于 `src/router/index.ts`：

- 使用传统路由配置方式
- 支持 `meta.title` 设置页面标题
- 预留 `meta.requiresAuth` 用于认证守卫

### 状态管理

Pinia Store 位于 `src/stores/`：

- `datasets.ts` - 知识库列表状态，包含 loading、error、datasets

### UI 组件

- `src/components/ui/` - 基础 UI 组件，使用 Tailwind CSS 样式
- `src/layouts/` - 布局组件，包含侧边栏和内容区

## 代码质量标准

### TypeScript / Vue

- 使用 TypeScript 编写 Vue 组件
- 组件使用 `<script setup lang="ts">` 语法
- Props 使用 `defineProps` + `withDefaults` 定义
- 类型定义放在 `src/types/` 目录

### 样式

- 使用 Tailwind CSS v4
- 组件样式使用 scoped CSS 或 Tailwind class
- 全局样式放在 `src/styles/`

### 代码格式化

- 使用 Biome 进行 lint 和 format
- 提交前运行 `pnpm check:fix` 确保代码风格一致

## 测试

测试框架使用 Vitest，配置文件为 `vitest.config.ts`。

**常用命令：**

```bash
pnpm test:unit              # 运行测试（监听模式）
pnpm test:unit -- --run     # 运行一次
pnpm test:unit -- --coverage # 运行并生成覆盖率报告
```

**测试文件组织：**

- 测试文件放在 `tests/` 目录
- 文件命名为 `*.test.ts` 或 `*.spec.ts`
- 组件测试使用 `@vue/test-utils` 的 `mount` 函数

**示例：**

```typescript
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import MyComponent from "@/components/MyComponent.vue";

describe("MyComponent", () => {
  it("renders correctly", () => {
    const wrapper = mount(MyComponent);
    expect(wrapper.text()).toContain("expected text");
  });
});
```

## 提交规范

遵循仓库根目录的 Conventional Commits 规范。

## 开发注意事项

- 修改 API 客户端时，确保类型定义同步更新
- 新增页面需在 `src/router/index.ts` 添加路由配置
- 新增 Store 需在 `src/stores/` 目录创建文件
