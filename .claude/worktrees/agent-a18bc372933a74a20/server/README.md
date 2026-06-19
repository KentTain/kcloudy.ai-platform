# 后端服务

本目录包含多种后端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 目录结构

```text
server/
├── config/                       # 共享配置文件
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
    │       └── schemas/          # DTO 模型
    │
    └── tests/                    # 测试目录
        └── {模块}/               # 模块测试
```

## 技术栈概览

| 技术栈 | 语言 | 框架 | 状态 | 文档 |
|--------|------|------|------|------|
| Python | Python 3.12 | FastAPI + SQLAlchemy 2.0 | ✅ 可用 | [README](python/README.md) |
| Rust | Rust 1.95+ | Axum + SQLx | ✅ 可用 | [README](rust/README.md) |
| Java | Java 21 | Spring Boot 3.x | 🚧 规划中 | - |
| .NET | .NET 8.0 | ASP.NET Core + EF Core | 🚧 规划中 | - |

## 统一架构

所有技术栈采用统一的 MVC 架构和基础设施：

### 架构分层

| 层级 | 职责 |
|------|------|
| Controller | HTTP 请求处理、参数校验、响应封装 |
| Service | 业务逻辑、事务管理 |
| Model | 数据模型、数据库操作 |

### 基础设施

| 组件 | 用途 |
|------|------|
| PostgreSQL + pgvector | 主数据库 + 向量检索 |
| Redis | 缓存 / 消息队列 / 发布订阅 |
| MinIO | 对象存储 |

### 统一 API

所有技术栈提供统一的健康检查端点：

```
GET /health → {"status": "healthy", "timestamp": "..."}
```

## 快速开始

### 1. 准备公共依赖

**PostgreSQL (含 pgvector)**

```bash
# Windows (scoop)
scoop install postgresql

# macOS
brew install postgresql@14

# 创建数据库
createdb demo
```

**Redis**

```bash
# Windows (scoop)
scoop install redis

# macOS
brew install redis

redis-server
redis-cli ping
```

### 2. 配置本地环境

```bash
cp server/config/application-local.yml.example server/config/application-local.yml
```

### 3. 启动服务

**Python 后端**

```bash
cd server/python
uv sync
uv run python manage.py runserver
# http://localhost:8000/health
```

**Rust 后端**

```bash
cd server/rust
cargo build
cargo run
# http://localhost:8000/health
```

## 配置管理

配置文件统一放置在 `server/config/` 目录下，各技术栈通过符号链接引用。

**配置优先级：** 环境变量 > 环境配置 > 基础配置

**环境选择：** 设置 `SERVICE_ENV` 环境变量（`local`/`dev`/`test`/`prod`）

## 开发指南

各技术栈的详细开发指南请参阅对应的 CLAUDE.md 文档：

- [整体开发指南](CLAUDE.md)
- [Python 开发指南](python/CLAUDE.md)
- [Rust 开发指南](rust/CLAUDE.md)

## 环境要求

| 技术栈 | 语言版本 | 包管理器 |
|--------|----------|----------|
| Python | 3.12+ | uv |
| Rust | 1.95+ | cargo |
| Java | 21+ | maven |
| .NET | 8.0+ | dotnet |

| 公共组件 | 版本 |
|----------|------|
| PostgreSQL | 14+ |
| Redis | 6+ |
| MinIO | Latest |

## License

Copyright © 2025 Moles. All Rights Reserved.
