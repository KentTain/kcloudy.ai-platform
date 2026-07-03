# AI 模块开发指南

本文件为 Claude Code 在 `web/vue/src/ai/` AI 对话模块中工作时提供指导。

## 模块定位

AI 模块提供 AI 对话功能，使用 Vercel AI SDK 标准协议与后端通信。支持多模型选择、流式对话、工具调用等特性。

## 目录职责

| 目录 | 职责 |
|------|------|
| api/ | API 函数（会话管理、模型列表） |
| composables/ | 组合式函数（useChat） |
| components/ | 模块专用组件（ModelSelector、ToolCallItem） |
| pages/ | 页面组件（ChatPage） |
| router/ | 模块路由配置 |
| stores/ | Pinia 状态管理（会话状态） |
| types/ | TypeScript 类型定义（基于 AI SDK 标准） |

## 页面组件

| 页面 | 路径 | 功能 |
|------|------|------|
| ChatPage | /ai | AI 对话界面，支持流式响应，右侧集成可伸缩会话列表 |

## 路由配置

| 路径 | 组件 | 权限 |
|------|------|------|
| /ai | ChatPage | requiresAuth |

## API 函数

### 会话管理

| 函数 | 说明 |
|------|------|
| getConversations | 获取会话列表 |
| deleteConversation | 删除指定会话 |

### 模型管理

| 函数 | 说明 |
|------|------|
| getModels | 获取可用模型列表（按提供商分组） |

## 核心类型

| 类型 | 说明 |
|------|------|
| UIMessage | AI SDK 标准 UI 消息格式 |
| AppUIMessage | 扩展的 UI 消息，用于前端显示 |
| UIMessagePart | 消息部分（text/image/tool-call/tool-result） |
| ModelConfig | 模型配置 |
| Conversation | 会话信息 |

## Composables

| 函数 | 说明 |
|------|------|
| useChat | 对话逻辑封装，处理消息发送、流式响应、工具调用 |

## 开发规则

- 使用 `<script setup lang="ts">` 语法
- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore`
- 页面使用 `AppPage` 组件作为骨架
- 消息格式遵循 Vercel AI SDK 标准

## 测试

```bash
pnpm test:unit tests/ai/unit/ --run
```
