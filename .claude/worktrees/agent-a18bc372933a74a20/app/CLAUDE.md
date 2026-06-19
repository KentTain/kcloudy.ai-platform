# CLAUDE.md

本文件为 Claude Code 在移动端应用目录工作时提供指导。

## 目录定位

`app/` 目录包含多种移动端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 | 详细文档 |
|--------|------|------|------|----------|
| Flutter | Dart 3.x | Flutter 3.x | 🚧 规划中 | - |
| React Native | TypeScript 5.x | React Native 0.7x | 🚧 规划中 | - |

## 架构规则

| 规则 | 说明 |
|------|------|
| 分层架构 | Screens → Components → Stores → API |
| 模块隔离 | 每个业务模块独立路由和状态 |

## 分层职责

| 层级 | 职责 |
|------|------|
| Screens | 页面组件，导航对应的视图 |
| Components | 可复用的 UI 组件 |
| Stores | 全局状态管理 |
| API | HTTP 请求封装 |
| Hooks | 可复用逻辑 |

## 环境要求

### Flutter

- Flutter SDK 3.x
- Dart 3.x

### React Native

- Node.js 22+
- pnpm 10.x
