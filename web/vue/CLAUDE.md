# Vue 前端指南

本文件为 Claude Code 在 Vue 前端项目中工作时提供指导。

## 项目定位

Vue 前端使用 Vue 3 + TypeScript + Vite 构建，提供 AI 助手平台演示界面。项目采用模块化结构，支持功能模块的独立开发。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3.5, TypeScript 5.8 |
| 构建 | Vite 6.x |
| 路由 | Vue Router 4.x |
| 状态管理 | Pinia 3.x |
| UI 组件库 | shadcn-vue |
| 无样式原语 | Radix Vue |
| 样式 | Tailwind CSS v4 |
| 代码质量 | Biome |
| 测试 | Vitest, @vue/test-utils |

## 模块导航

| 模块 | 定位 | 详细文档 |
|------|------|----------|
| framework | 基础设施：UI框架、路由、状态管理 | [src/framework/CLAUDE.md](src/framework/CLAUDE.md) |
| tenant | 租户管理模块 | [src/tenant/CLAUDE.md](src/tenant/CLAUDE.md) |
| iam | 身份认证与权限模块 | [src/iam/CLAUDE.md](src/iam/CLAUDE.md) |
| demo | 业务演示模块 | [src/demo/CLAUDE.md](src/demo/CLAUDE.md) |

## 依赖边界

```
demo / iam / tenant ──▶ framework
framework ──X──▶ demo / iam / tenant
```

- 业务模块可以依赖 `framework`
- `framework` 禁止依赖业务模块

## 模块结构规范

每个业务模块必须包含：

| 文件/目录 | 用途 |
|-----------|------|
| `index.ts` | 模块入口，导出 ModuleDescriptor |
| `router/index.ts` | 模块路由配置（必需） |
| `api/` | API 函数 |
| `types/` | TypeScript 类型定义 |
| `pages/` | 页面组件 |
| `components/` | 模块专用组件 |
| `stores/` | Pinia 状态管理 |

## 核心命令

```bash
# 启动开发服务器
pnpm dev

# 生产构建
pnpm build

# 代码检查
pnpm check
pnpm check:fix

# 测试
pnpm test:unit
pnpm test:unit -- --run
```

## 开发约束

- TypeScript 版本：5.8
- 行宽：100 字符
- 组件语法：`<script setup lang="ts">`
- API 请求使用 `@/framework/api/client` 封装

## 测试

测试文件位于 `tests/` 目录，按模块组织，详见 [tests/CLAUDE.md](tests/CLAUDE.md)。

### 测试目录结构

| 目录 | 说明 |
|------|------|
| tests/components/ | 通用组件测试 |
| tests/framework/ | Framework 模块测试 |
| tests/tenant/ | Tenant 模块测试 |
| tests/iam/ | IAM 模块测试 |
| tests/ai/ | AI 模块测试 |
| tests/demo/ | Demo 模块测试 |

### 测试命令

```bash
# 运行所有测试
pnpm test:unit

# 运行特定模块测试
pnpm test:unit tests/ai/ --run
pnpm test:unit tests/iam/ --run
pnpm test:unit tests/framework/ --run

# 生成覆盖率报告
pnpm test:unit -- --coverage
```

## 环境要求

- Node.js 22+
- pnpm 10+

详细开发指南见 [src/CLAUDE.md](src/CLAUDE.md)，完整使用示例见 [README.md](README.md)。
