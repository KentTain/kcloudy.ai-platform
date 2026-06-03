# CLAUDE.md

本文件为 Claude Code 在后端服务目录工作时提供指导。

## 目录定位

`server/` 目录包含多种后端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 | 详细文档 |
|--------|------|------|------|----------|
| Python | Python 3.12 | FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic + LangChain | ✅ 可用 | [python/CLAUDE.md](python/CLAUDE.md) |
| Rust | Rust 1.95+ | Axum + SQLx + serde + Tokio + LangChainRust | ✅ 可用 | [rust/CLAUDE.md](rust/CLAUDE.md) |
| Java | Java 21 | Spring Boot 3.x + MyBatis + LangChain4j | 🚧 规划中 | - |
| .NET | .NET 8.0 | ASP.NET Core + EF Core + LangChain.NET | 🚧 规划中 | - |

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

## 架构规则

| 规则 | 说明 |
|------|------|
| 分层架构 | Controller → Service → Model |
| Schema 隔离 | 每个模块独立 PostgreSQL schema |
| 依赖边界 | 业务模块可依赖 framework，反向禁止 |

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

## 环境要求

| 技术栈 | 版本要求 | 包管理器 |
|--------|----------|----------|
| Python | 3.12+ | uv |
| Rust | 1.95+ | cargo |
| Java | 21+ | maven |
| .NET | 8.0+ | dotnet cli |

公共依赖：PostgreSQL 14+、Redis 6+、MinIO（可选）
