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
| Rust | Rust 1.75+ | Axum + SQLx | ✅ 可用 | [README](rust/README.md) |
| Java | Java 21 | Spring Boot 3.x + MyBatis | 🚧 规划中 | - |
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
| Rust | 1.75+ | cargo |
| Java | 21+ | maven |
| .NET | 8.0+ | dotnet |

| 公共组件 | 版本 |
|----------|------|
| PostgreSQL | 14+ |
| Redis | 6+ |
| MinIO | Latest |

## License

Copyright © 2025 Moles. All Rights Reserved.
