# 移动端应用

本目录包含多种移动端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 目录结构

```text
app/
└── {技术栈}/                     # 技术栈目录
    ├── src/                      # 源码目录
    │   └── {模块}/               # 业务模块
    │       ├── api/              # API 客户端
    │       ├── components/       # 通用组件
    │       ├── screens/          # 页面组件
    │       ├── navigation/       # 导航配置
    │       ├── stores/           # 状态管理
    │       └── types/            # 类型定义
    │
    └── tests/                    # 测试目录
        └── {模块}/               # 模块测试
```

## 技术栈概览

| 技术栈 | 语言 | 框架 | 状态 | 文档 |
|--------|------|------|------|------|
| Flutter | Dart 3.x | Flutter 3.x | 🚧 规划中 | - |
| React Native | TypeScript 5.x | React Native 0.7x | 🚧 规划中 | - |

## 统一架构

所有技术栈采用统一的移动端架构和基础设施：

### 架构分层

| 层级 | 职责 |
|------|------|
| Screens | 页面组件，导航对应的视图 |
| Components | 可复用的 UI 组件 |
| Stores | 全局状态管理 |
| API | HTTP 请求封装 |
| Hooks | 可复用的组合式函数 |

### 统一 API

移动端通过 HTTP 请求访问后端 API：

```
/api/*    → 后端 API
/health/* → 健康检查
```

## 快速开始

### Flutter

```bash
cd app/flutter
flutter pub get
flutter run
```

### React Native

```bash
cd app/react-native
pnpm install
pnpm start
```

## 开发指南

各技术栈的详细开发指南请参阅对应的 CLAUDE.md 文档：

- [整体开发指南](CLAUDE.md)
- [Flutter 开发指南](flutter/CLAUDE.md) (规划中)
- [React Native 开发指南](react-native/CLAUDE.md) (规划中)

## 环境要求

| 技术栈 | 语言版本 | 包管理器 |
|--------|----------|----------|
| Flutter | Dart 3.x | pub |
| React Native | Node.js 22+ | pnpm 10.x |

## License

Copyright © 2025 Moles. All Rights Reserved.
