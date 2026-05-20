# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在后端服务目录工作时提供指导。

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

## 技术选型

| 技术栈 | 核心技术 | 详细文档 |
|--------|----------|----------|
| Python | FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic + LangChain | [python/CLAUDE.md](python/CLAUDE.md) |
| Rust | Axum + SQLx + serde + Tokio + LangChainRust | [rust/CLAUDE.md](rust/CLAUDE.md) |
| Java | Spring Boot 3.x + MyBatis + LangChain4j | [java/CLAUDE.md](java/CLAUDE.md) (规划中) |
| .NET | ASP.NET Core 8.0 + EF Core + LangChain.NET | [netcore/CLAUDE.md](netcore/CLAUDE.md) (规划中) |

## 项目结构

所有技术栈采用统一的 MVC 架构：

```text
server/
├── config/                       # 共享配置文件目录
│   ├── application.yml           # 基础配置
│   ├── application-local.yml.example # 本地配置示例
│   └── application-local.yml     # 本地配置（不提交）
└── {技术栈}/                     # 技术栈项目目录
    ├── src/                      # 源码
    │   ├── controllers/          # API 控制器
    │   ├── services/             # 业务逻辑层
    │   ├── models/               # 数据库模型
    │   ├── schemas/              # DTO 模型
    │   ├── configs/              # 配置管理
    │   ├── db/                   # 数据库引擎
    │   ├── migrations/           # 数据库迁移
    │   └── utils/                # 工具函数
    ├── tests/                    # 测试文件
    ├── config/                   # 配置（引用共享配置）
    ├── CLAUDE.md                 # 开发指南
    └── README.md                 # 说明文档
```

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

### API 文档

| 技术栈 | 文档端点 |
|--------|----------|
| Python | `/docs` (Swagger), `/redoc` (ReDoc) |
| Rust | 需手动配置 |
| Java | `/swagger-ui.html` |
| .NET | `/swagger` |

### RESTful 规范

- URL 设计：资源导向，小写连字符分隔
- HTTP 方法：GET 查询、POST 创建、PUT 更新、DELETE 删除
- 响应格式：统一 JSON 结构，包含 `code`、`message`、`data` 字段

## 配置管理

### 配置文件结构

```text
server/config/                   # 共享配置文件目录
├── application.yml              # 基础配置（提交）
├── application-local.yml.example # 本地配置示例（提交）
└── application-local.yml        # 本地配置（不提交）

server/{技术栈}/config/          # 符号链接指向 server/config/
```

### 符号链接配置

```bash
# Linux/macOS
cd server/python && ln -s ../config config
cd server/rust && ln -s ../config config

# Windows (需要管理员权限)
cd server\python && mklink /D config ..\config
cd server\rust && mklink /D config ..\config
```

### 配置优先级

1. 环境变量覆盖（最高优先级）
2. 环境特定配置文件 `application-{env}.yml`
3. 基础配置文件 `application.yml`

### 环境选择

通过 `SERVICE_ENV` 环境变量指定运行环境：`local`、`dev`、`test`、`prod`

## 开发规范

- 遵循各语言的社区规范和最佳实践
- 统一使用 Conventional Commits 提交规范
- 保持各技术栈 API 行为一致性

## 环境要求

### 公共依赖

- PostgreSQL 14+ (含 pgvector 扩展)
- Redis 6+
- MinIO (可选，对象存储)

### 语言环境

| 技术栈 | 版本要求 | 包管理器 |
|--------|----------|----------|
| Python | 3.12+ | uv |
| Rust | 1.75+ | cargo |
| Java | 21+ | maven |
| .NET | 8.0+ | dotnet cli |

## License

Copyright © 2025 Moles. All Rights Reserved.
