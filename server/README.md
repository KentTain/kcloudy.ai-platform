# 后端服务

本目录包含多种后端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 目录结构

```text
server/
├── config/                   # 共享配置文件
│   ├── application.yml          # 基础配置
│   ├── application-local.yml.example # 本地配置示例
│   └── application-local.yml    # 本地配置（不提交）
├── python/                   # Python 后端 ✅
├── rust/                     # Rust 后端 ✅
├── java/                     # Java 后端 🚧
└── netcore/                  # .NET 后端 🚧
```

## 技术栈概览

| 技术栈 | 语言 | 框架 | 状态 | 文档 |
|--------|------|------|------|------|
| Python | Python 3.12 | FastAPI + SQLAlchemy 2.0 | ✅ 可用 | [README](python/README.md) |
| Rust | Rust 1.95+ | Axum + SQLx | ✅ 可用 | [README](rust/README.md) |
| Java | Java 21 | Spring Boot 3.x + MyBatis | 🚧 规划中 | - |
| .NET | .NET 8.0 | ASP.NET Core + EF Core | 🚧 规划中 | - |

## 技术栈对比

### 完整技术选型

| 类别 | Python | Rust | Java | .NET |
|------|--------|------|------|------|
| **Web 框架** | FastAPI 0.115 | Axum 0.8 | Spring Boot 3.x | ASP.NET Core 8.0 |
| **ORM** | SQLAlchemy 2.0 | SQLx 0.8 | MyBatis / Hibernate | Entity Framework Core 8.0 |
| **数据库迁移** | Alembic 1.14 | SQLx migrations | Flyway / Liquibase | EF Core Migrations |
| **数据验证** | Pydantic 2.10 | serde + validator | Bean Validation | FluentValidation |
| **AI 框架** | LangChain 1.3 + LangGraph 1.2 | LangChainRust | LangChain4j | LangChain.NET |
| **测试框架** | pytest + pytest-asyncio | cargo-nextest | JUnit 5 | xUnit |
| **异步运行时** | asyncio | Tokio | Virtual Threads | Task Parallel Library |
| **依赖注入** | 内置 / dependency-injector | 内置 | Spring IoC | Microsoft DI |
| **配置管理** | PyYAML | config-rs | Spring Config | appsettings.json |
| **HTTP 客户端** | httpx | reqwest | RestTemplate / WebClient | HttpClient |
| **JSON 序列化** | orjson | serde_json | Jackson | System.Text.Json |
| **Linter/Format** | Ruff | rustfmt + clippy | SpotBugs / Checkstyle | StyleCop |

### Web 框架对比

| 特性 | Python (FastAPI) | Rust (Axum) | Java (Spring Boot) | .NET (ASP.NET Core) |
|------|------------------|-------------|--------------------|--------------------|
| 类型系统 | 动态 + 类型提示 | 静态 | 静态 | 静态 |
| 性能 | 中等 | 极高 | 高 | 高 |
| 异步支持 | 原生 async/await | 原生 async/await | Virtual Threads | async/await |
| API 文档 | 自动生成 (Swagger) | 需手动配置 | 自动生成 | 自动生成 |
| 学习曲线 | 平缓 | 陡峭 | 中等 | 中等 |
| 生态成熟度 | 高 | 中 | 极高 | 高 |

### ORM 对比

| 特性 | Python (SQLAlchemy) | Rust (SQLx) | Java (MyBatis) | .NET (EF Core) |
|------|---------------------|-------------|----------------|----------------|
| 类型 | 全功能 ORM | 编译时检查 SQL | SQL 映射框架 | 全功能 ORM |
| 类型安全 | 运行时 | 编译时 | 运行时 | 编译时 |
| 异步支持 | ✅ 原生 | ✅ 原生 | ✅ 需要 | ✅ 原生 |
| 迁移工具 | Alembic | SQLx migrations | Flyway | 内置 |
| 复杂查询 | 强大 | 灵活 SQL | 灵活 XML/注解 | LINQ |
| 学习曲线 | 中等 | 中等 | 简单 | 中等 |

### 数据验证对比

| 特性 | Python (Pydantic) | Rust (serde) | Java (Bean Validation) | .NET (FluentValidation) |
|------|-------------------|--------------|------------------------|------------------------|
| 验证方式 | 装饰器 | derive 宏 | 注解 | Fluent API |
| 运行时检查 | ✅ | ❌ 编译时 | ✅ | ✅ |
| 自动转换 | ✅ 类型强制转换 | ✅ 反序列化 | ❌ | ❌ |
| 错误信息 | 结构化 | 自定义 | 默认 | 自定义 |
| OpenAPI 集成 | ✅ 自动 | 需手动 | ✅ | ✅ |

### AI 框架对比

| 特性 | Python (LangChain) | Rust (LangChainRust) | Java (LangChain4j) | .NET (LangChain.NET) |
|------|--------------------|-----------------------|--------------------|-----------------------|
| 成熟度 | 最高 | 中等 | 高 | 中等 |
| 模型支持 | 全面 | 主要模型 | 主要模型 | 主要模型 |
| 向量数据库 | 全面 | 基本 | 基本 | 基本 |
| Agent 支持 | LangGraph | 基本 | 基本 | 基本 |
| 文档质量 | 完善 | 完善 | 完善 | 完善 |

### 测试框架对比

| 特性 | Python (pytest) | Rust (nextest) | Java (JUnit 5) | .NET (xUnit) |
|------|-----------------|----------------|----------------|--------------|
| 并行测试 | 插件支持 | ✅ 内置 | 需配置 | ✅ 内置 |
| 异步测试 | ✅ pytest-asyncio | ✅ 内置 | ✅ | ✅ |
| Mock 支持 | pytest-mock | mockall | Mockito | Moq |
| 参数化测试 | ✅ @pytest.mark.parametrize | ✅ #[test_case] | ✅ @ParameterizedTest | ✅ [Theory] |
| Fixtures | ✅ 强大 | 无 | 无 | 共享上下文 |
| 覆盖率报告 | pytest-cov | cargo-tarpaulin | JaCoCo | coverlet |

### 项目结构差异

| 目录/文件 | Python | Rust | Java | .NET |
|-----------|--------|------|------|------|
| 源码目录 | `src/demo/` | `src/` | `src/main/java/` | `src/` |
| 测试目录 | `tests/` | `src/` 嵌入 | `src/test/java/` | `tests/` |
| 配置文件 | `config/application.yml` | `config/` | `application.yml` | `appsettings.json` |
| 入口文件 | `run.py` | `main.rs` | `Application.java` | `Program.cs` |
| 依赖管理 | `pyproject.toml` | `Cargo.toml` | `pom.xml` | `.csproj` |

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

# 启动并验证
redis-server
redis-cli ping
```

**MinIO (可选)**

```bash
# Docker 方式
docker run -d -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### 2. 配置本地环境

```bash
# 复制配置模板
cp server/config/application-local.yml.example server/config/application-local.yml

# 编辑配置文件，填写数据库连接信息
```

### 3. 启动服务

选择一个技术栈启动：

**Python 后端**

```bash
cd server/python
uv sync
uv run runserver
# 访问 http://localhost:8000/health
```

**Rust 后端**

```bash
cd server/rust
cargo build
cargo run
# 访问 http://localhost:8000/health
```

详细说明请参阅各技术栈的 README 文档。

## 配置管理

配置文件统一放置在 `server/config/` 目录下，各技术栈通过**符号链接**引用：

```text
server/config/                   # 共享配置文件目录
├── application.yml              # 基础配置
├── application-local.yml.example # 本地配置示例
└── application-local.yml        # 本地配置（不提交）

server/python/config/            # 符号链接 → ../config
server/rust/config/              # 符号链接 → ../config
```

### 创建符号链接

```bash
# Linux/macOS
cd server/python && ln -s ../config config
cd server/rust && ln -s ../config config

# Windows (需要管理员权限)
cd server\python && mklink /D config ..\config
cd server\rust && mklink /D config ..\config

# Windows PowerShell (需要管理员权限)
New-Item -ItemType SymbolicLink -Path "server\python\config" -Target "server\config"
New-Item -ItemType SymbolicLink -Path "server\rust\config" -Target "server\config"
```

> **注意：** Windows 创建符号链接需要管理员权限。修改任意技术栈的配置文件会同步到所有技术栈。

### 本地开发

```bash
# 复制配置模板
cp server/config/application-local.yml.example server/config/application-local.yml

# 编辑配置文件
vim server/config/application-local.yml
```

### 配置优先级

环境变量 > 环境配置 > 基础配置

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
