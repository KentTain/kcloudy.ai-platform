# CLAUDE.md

本文件为 Claude Code 在移动端应用目录工作时提供指导。

## 目录概述

`app/` 目录包含多种移动端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范，提供可对比、可学习的多技术栈参考。

**核心目标：** 提供功能等价的多技术栈移动端实现，便于技术选型对比和团队学习。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 |
|--------|------|------|------|
| Flutter | Dart 3.x | Flutter 3.x | 🚧 规划中 |
| React Native | TypeScript 5.x | React Native 0.7x | 🚧 规划中 |

**各技术栈详细文档：**

- Flutter: [flutter/CLAUDE.md](flutter/CLAUDE.md) (规划中)
- React Native: [react-native/CLAUDE.md](react-native/CLAUDE.md) (规划中)

## 项目结构

```text
app/
└── {技术栈}/                     # 技术栈目录
    ├── src/                      # 源码目录
    │   ├── api/                  # API 客户端
    │   ├── components/           # 通用组件
    │   ├── screens/              # 页面组件
    │   │   └── {模块}/           # 业务模块页面
    │   ├── navigation/           # 导航配置
    │   ├── stores/               # 状态管理
    │   │   └── {模块}/           # 业务模块状态
    │   ├── styles/               # 全局样式
    │   ├── types/                # 类型定义
    │   └── App.tsx/App.ts        # 根组件
    │
    └── tests/                    # 测试目录
        ├── components/           # 组件测试
        └── stores/               # Store 测试
```

## 技术选型

| 技术栈 | 核心技术 | 详细文档 |
|--------|----------|----------|
| Flutter | Flutter 3.x + Dart + Riverpod + GoRouter | [flutter/CLAUDE.md](flutter/CLAUDE.md) (规划中) |
| React Native | React Native 0.7x + TypeScript + Zustand + React Navigation | [react-native/CLAUDE.md](react-native/CLAUDE.md) (规划中) |

## 分层架构

| 层级 | 职责 |
|------|------|
| Screens | 页面组件，导航对应的视图 |
| Components | 可复用的 UI 组件 |
| Stores | 全局状态管理 |
| API | HTTP 请求封装 |
| Hooks | 可复用逻辑 |

## 统一基础设施

| 组件 | 用途 |
|------|------|
| TypeScript/Dart | 类型系统 |
| HTTP 客户端 | API 请求 |
| 状态管理 | 全局状态 |
| 导航框架 | 路由管理 |

## API 规范

移动端通过 HTTP 请求访问后端 API：

- `/api/*` → 后端 API
- `/health` → 健康检查

### RESTful 规范

- URL 设计：资源导向，小写连字符分隔
- HTTP 方法：GET 查询、POST 创建、PUT 更新、DELETE 删除
- 响应格式：统一 JSON 结构，包含 `code`、`message`、`data` 字段

## 环境要求

### Flutter

- Flutter SDK 3.x
- Dart 3.x

### React Native

- Node.js 22+
- pnpm 10.x

## License

Copyright © 2025 Moles. All Rights Reserved.
