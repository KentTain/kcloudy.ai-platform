# InitProject - 最小化 AI 助手平台

本项目是一个多技术栈的 AI 助手平台演示项目，提供多种后端和前端技术选型，便于学习和对比不同技术栈的实现方式。

## 项目结构

```text
init_project/
├── server/                    # 后端服务
│   ├── python/                # Python 后端（FastAPI）
│   ├── java/                  # Java 后端（Spring Boot）
│   └── rust/                  # Rust 后端（Actix-web）
├── web/                       # 前端 PC 项目
│   ├── vue/                   # Vue 3 + TypeScript
│   └── react/                 # React + TypeScript
├── app/                       # 前端 Mobile 项目
├── docker/                    # Docker 部署配置
└──  docs/                      # 项目文档
```

## 技术选型

### 后端服务 (server/)

| 语言 | 框架 | 目录 | 状态 |
|------|------|------|------|
| Python | FastAPI + SQLAlchemy | [server/python](server/python) | ✅ 可用 |
| Java | Spring Boot | [server/java](server/java) | 🚧 规划中 |
| Rust | Actix-web | [server/rust](server/rust) | 🚧 规划中 |

### 前端 PC 项目 (web/)

| 框架 | 语言 | 目录 | 状态 |
|------|------|------|------|
| Vue | TypeScript | [web/vue](web/vue) | 🚧 规划中 |
| React | TypeScript | [web/react](web/react) | 🚧 规划中 |

### 前端 Mobile 项目 (app/)

| 框架 | 语言 | 目录 | 状态 |
|------|------|------|------|
| Flutter | Dart | [app/flutter](app/flutter) | 🚧 规划中 |
| React Native | TypeScript | [app/react-native](app/react-native) | 🚧 规划中 |

## 快速开始

### Python 后端

```bash
cd server/python

# 安装依赖
uv sync

# 配置
cp config/application-local.yml.example config/application-local.yml

# 启动服务
uv run runserver
```

访问：<http://localhost:8000/docs>

详见 [server/python/README.md](server/python/README.md)

## 环境要求

### 后端

- Python 3.12+ / uv
- Java 21+ / Maven (规划中)
- Rust 1.75+ / Cargo (规划中)
- PostgreSQL 14+
- Redis 6+

### 前端

- Node.js 22+
- pnpm 10+

## 功能特点

### 核心能力

- **RESTful API 设计**：统一的 JSON 响应格式
- **AI 框架集成**：LangChain 1.3.0、LangGraph 1.2.0
- **数据库支持**：PostgreSQL + pgvector（向量搜索）
- **缓存支持**：Redis 高性能缓存
- **完善的错误处理**：全局异常处理和自动错误追踪

### 数据与存储

- **数据库集成**：SQLAlchemy 2.0 + Alembic 迁移
- **分层配置**：基于 YAML 的多环境配置系统

## 模块文档

| 模块 | 文档 | 说明 |
| ------ | ------ | ------ |
| Python 后端 | [server/python/README.md](server/python/README.md) | FastAPI 后端功能、安装配置 |
| Python 测试 | [server/python/tests/README.md](server/python/tests/README.md) | 测试框架、运行测试 |
| Docker 部署 | [docker/README.md](docker/README.md) | Docker Compose 部署指南 |

## License

Copyright © 2025 Moles. All Rights Reserved.
