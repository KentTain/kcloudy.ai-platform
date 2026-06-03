# Demo 模块开发指南

本文件为 Claude Code 在 `web/vue/src/demo/` 业务演示模块中工作时提供指导。

## 模块定位

Demo 模块是 AI 助手平台的业务演示模块，包含知识库管理、健康检查、EventBus 示例等功能页面。

## 目录职责

| 目录 | 职责 |
|------|------|
| api/ | API 函数（health、datasets） |
| pages/ | 页面组件（Home、Health、Datasets、EventBusDemo） |
| router/ | 模块路由配置 |
| stores/ | Pinia 状态管理（datasets） |
| types/ | TypeScript 类型定义 |

## 页面组件

| 页面 | 路径 | 功能 |
|------|------|------|
| HomePage | / | 平台介绍和功能特性 |
| HealthPage | /health | 后端健康状态检查 |
| DatasetsPage | /datasets | 知识库列表和 CRUD |
| EventBusDemoPage | /demo/event-bus | EventBus 使用示例 |

## 开发规则

- 使用 `<script setup lang="ts">` 语法
- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore`
- 页面使用 `AppPage` 组件作为骨架

## 测试

```bash
pnpm test:unit tests/demo/ --run
```
