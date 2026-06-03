# AI Platform - 多技术栈 AI 助手平台

本项目是一个多技术栈的 AI 助手平台演示项目，提供多种后端和前端技术选型，便于学习和对比不同技术栈的实现方式。

## 项目结构

```text
kcloudy.ai-platform/
├── server/                    # 后端服务
│   ├── python/                # Python 后端（FastAPI）✅ 可用
│   ├── rust/                  # Rust 后端（Axum）✅ 可用
│   ├── java/                  # Java 后端（Spring Boot）🚧 规划中
│   └── netcore/               # .NET 后端（ASP.NET Core）🚧 规划中
├── web/                       # 前端 PC 项目
│   ├── vue/                   # Vue 3 + TypeScript ✅ 可用
│   └── react/                 # React + TypeScript 🚧 规划中
├── app/                       # 前端 Mobile 项目
│   ├── flutter/               # Flutter 🚧 规划中
│   └── react-native/          # React Native 🚧 规划中
├── docker/                    # Docker 部署配置
└── docs/                      # 项目文档
```

## 技术选型

### 后端服务 (server/)

| 语言 | 框架 | 目录 | 状态 | 文档 |
|------|------|------|------|------|
| Python | FastAPI + SQLAlchemy | [server/python](server/python) | ✅ 可用 | [README](server/python/README.md) |
| Rust | Axum + SQLx | [server/rust](server/rust) | ✅ 可用 | [README](server/rust/README.md) |
| Java | Spring Boot | [server/java](server/java) | 🚧 规划中 | - |
| .NET | ASP.NET Core | [server/netcore](server/netcore) | 🚧 规划中 | - |

### 前端 PC 项目 (web/)

| 框架 | 语言 | 目录 | 状态 | 文档 |
|------|------|------|------|------|
| Vue | TypeScript | [web/vue](web/vue) | ✅ 可用 | [README](web/vue/README.md) |
| React | TypeScript | [web/react](web/react) | 🚧 规划中 | - |

### 前端 Mobile 项目 (app/)

| 框架 | 语言 | 目录 | 状态 | 文档 |
|------|------|------|------|------|
| Flutter | Dart | [app/flutter](app/flutter) | 🚧 规划中 | - |
| React Native | TypeScript | [app/react-native](app/react-native) | 🚧 规划中 | - |

## 快速开始

### Python 后端

```bash
cd server/python

# 安装依赖
uv sync

# 配置
cp config/application-local.yml.example config/application-local.yml

# 启动服务
uv run python manage.py runserver
```

访问：<http://localhost:8000/docs>

详见 [server/python/README.md](server/python/README.md)

### Vue 前端

```bash
cd web/vue

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

访问：<http://localhost:5173>

详见 [web/vue/README.md](web/vue/README.md)

## 环境要求

### 后端

- Python 3.12+ / uv
- Rust 1.95+ / Cargo
- PostgreSQL 14+
- Redis 6+

### 前端

- Node.js 22+
- pnpm 10+

## 功能特点

### 核心能力

- **RESTful API 设计**：统一的 JSON 响应格式
- **AI 框架集成**：LangChain、LangGraph
- **数据库支持**：PostgreSQL + pgvector（向量搜索）
- **缓存支持**：Redis 高性能缓存
- **完善的错误处理**：全局异常处理和自动错误追踪

### 架构特性

- **模块化单体架构**：支持从单体到微服务的平滑过渡
- **模块级 Schema 隔离**：每个模块独立 PostgreSQL schema
- **模块动态加载**：按需加载业务模块

## 模块文档

| 模块 | 文档 | 说明 |
|------|------|------|
| Python 后端 | [server/python/README.md](server/python/README.md) | FastAPI 后端功能、安装配置 |
| Vue 前端 | [web/vue/README.md](web/vue/README.md) | Vue 3 前端功能、安装配置 |
| Docker 部署 | [docker/README.md](docker/README.md) | Docker Compose 部署指南 |

## 开发指南

各模块的 AI 助手开发指南请参阅对应的 CLAUDE.md 文档：

- [整体开发指南](CLAUDE.md)
- [后端开发指南](server/CLAUDE.md)
- [前端开发指南](web/CLAUDE.md)

## License

Copyright © 2025 Moles. All Rights Reserved.
