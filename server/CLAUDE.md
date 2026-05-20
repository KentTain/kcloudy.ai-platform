# CLAUDE.md

本文件为 Claude Code 在后端服务目录工作时提供指导。

## 目录概述

`server/` 目录包含多种后端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范，提供可对比、可学习的多技术栈参考。

**核心目标：** 提供功能等价的多技术栈后端实现，便于技术选型对比和团队学习。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 |
|--------|------|------|------|
| Python | Python 3.12 | FastAPI + SQLAlchemy 2.0 | ✅ 可用 |
| Rust | Rust 1.95+ | Axum + SQLx | ✅ 可用 |
| Java | Java 21 | Spring Boot 3.x | 🚧 规划中 |
| .NET | .NET 8.0 | ASP.NET Core + EF Core | 🚧 规划中 |

**各技术栈详细文档：**

- Python: [python/CLAUDE.md](python/CLAUDE.md)
- Rust: [rust/CLAUDE.md](rust/CLAUDE.md)
- Java: [java/CLAUDE.md](java/CLAUDE.md) (规划中)
- .NET: [netcore/CLAUDE.md](netcore/CLAUDE.md) (规划中)

## 项目结构

```text
server/
├── config/                       # 共享配置文件目录
│   ├── application.yml           # 基础配置
│   ├── application-local.yml.example # 本地配置示例
│   └── application-local.yml     # 本地配置（不提交）
│
└── {技术栈}/                     # 技术栈目录
    ├── src/                      # 源码目录
    │   └── {模块}/               # 业务模块
    │       ├── controllers/      # API 控制器
    │       ├── services/         # 业务逻辑层
    │       ├── models/           # 数据库模型
    │       ├── schemas/          # DTO 模型
    │       └── ...
    │
    └── tests/                    # 测试目录
        └── {模块}/               # 模块测试
            ├── fixtures/         # 测试夹具
            ├── unit/             # 单元测试
            └── integration/      # 集成测试
```

## 技术选型

| 技术栈 | 核心技术 | 详细文档 |
|--------|----------|----------|
| Python | FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic + LangChain | [python/CLAUDE.md](python/CLAUDE.md) |
| Rust | Axum + SQLx + serde + Tokio + LangChainRust | [rust/CLAUDE.md](rust/CLAUDE.md) |
| Java | Spring Boot 3.x + MyBatis + LangChain4j | [java/CLAUDE.md](java/CLAUDE.md) (规划中) |
| .NET | ASP.NET Core 8.0 + EF Core + LangChain.NET | [netcore/CLAUDE.md](netcore/CLAUDE.md) (规划中) |

## MVC 分层架构

| 层级 | 职责 |
|------|------|
| Controller | HTTP 请求处理：路由、参数校验、响应封装 |
| Service | 业务逻辑：核心业务、事务管理、缓存策略 |
| Model | 数据模型：ORM 映射、数据库操作 |

## 统一基础设施

| 组件 | 用途 |
|------|------|
| PostgreSQL + pgvector | 主数据库：关系数据存储 + 向量检索 |
| Redis | 缓存 / 队列 / 发布订阅 |
| MinIO | 对象存储：文件、图片等非结构化数据 |

## API 规范

### 健康检查端点

所有技术栈必须提供统一的健康检查 API：

```
GET /health → {"status": "healthy", "timestamp": "..."}
```

### RESTful 规范

- URL 设计：资源导向，小写连字符分隔
- HTTP 方法：GET 查询、POST 创建、PUT 更新、DELETE 删除
- 响应格式：统一 JSON 结构，包含 `code`、`message`、`data` 字段

## 配置管理

配置文件统一放置在 `server/config/` 目录下，各技术栈通过符号链接引用。

**配置优先级：** 环境变量 > 环境配置 > 基础配置

**环境选择：** 通过 `SERVICE_ENV` 环境变量指定：`local`、`dev`、`test`、`prod`

## 环境要求

### 公共依赖

- PostgreSQL 14+ (含 pgvector 扩展)
- Redis 6+
- MinIO (可选，对象存储)

### 语言环境

| 技术栈 | 版本要求 | 包管理器 |
|--------|----------|----------|
| Python | 3.12+ | uv |
| Rust | 1.95+ | cargo |
| Java | 21+ | maven |
| .NET | 8.0+ | dotnet cli |

## License

Copyright © 2025 Moles. All Rights Reserved.
