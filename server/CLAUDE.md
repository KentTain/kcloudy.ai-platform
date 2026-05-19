# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在后端服务目录工作时提供指导。

## 目录概述

`server/` 目录包含多种后端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范，提供可对比、可学习的多技术栈参考。

**核心目标：** 提供功能等价的多技术栈后端实现，便于技术选型对比和团队学习。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 |
|--------|------|------|------|
| Python | Python 3.12 | FastAPI + SQLAlchemy 2.0 | ✅ 可用 |
| Rust | Rust 1.75+ | Axum + SQLx | ✅ 可用 |
| Java | Java 21 | Spring Boot 3.x | 🚧 规划中 |
| .NET | .NET 8.0 | ASP.NET Core + EF Core | 🚧 规划中 |

**各技术栈详细文档：**

- Python: [python/CLAUDE.md](python/CLAUDE.md)
- Rust: [rust/CLAUDE.md](rust/CLAUDE.md)
- Java: [java/CLAUDE.md](java/CLAUDE.md) (规划中)
- .NET: [netcore/CLAUDE.md](netcore/CLAUDE.md) (规划中)

## 统一架构设计

所有技术栈采用统一的 MVC 架构和项目结构：

```text
server/
├── config/                       # 共享配置文件目录
│   ├── application.yml              # 基础配置
│   ├── application-local.yml.example # 本地开发配置示例
│   └── application-local.yml        # 本地开发配置（不提交）
└── {技术栈}/                     # 技术栈项目目录
    ├── src/{模块}/                  # 源码模块（framework、examples、auth、user 等）
    │   ├── components/              # 可插拔组件框架
    │   ├── controllers/             # API 控制器
    │   ├── services/                # 业务逻辑层
    │   ├── models/                  # 数据库模型
    │   ├── schemas/                 # DTO 模型
    │   ├── configs/                 # 配置管理
    │   ├── common/                  # 通用模块
    │   ├── db/                      # 数据库引擎
    │   ├── migrations/              # 数据库迁移
    │   ├── core/                    # 核心框架
    │   └── utils/                   # 工具函数
    ├── tests/                       # 测试文件
    ├── config/                      # 配置（引用共享配置）
    ├── scripts/                     # 开发脚本
    ├── CLAUDE.md                    # 开发指南
    └── README.md                    # 说明文档
```

### MVC 分层架构

| 层级 | 职责 | 说明 |
|------|------|------|
| Controller | HTTP 请求处理 | 路由、参数校验、响应封装 |
| Service | 业务逻辑 | 核心业务、事务管理、缓存策略 |
| Model | 数据模型 | ORM 映射、数据库操作 |

## 统一基础设施

所有技术栈共享以下基础设施组件：

| 组件 | 用途 | 说明 |
|------|------|------|
| PostgreSQL + pgvector | 主数据库 | 关系数据存储 + 向量检索 |
| Redis | 缓存 / 队列 / 发布订阅 | 多用途中间件 |
| MinIO | 对象存储 | 文件、图片等非结构化数据 |

### 连接配置示例

```yaml
# 数据库
database:
  url: postgresql://postgres:postgres@localhost:5432/demo

# Redis
redis:
  url: redis://localhost:6379/0

# MinIO
minio:
  endpoint: localhost:9000
  access_key: minioadmin
  secret_key: minioadmin
  bucket: demo
```

## 统一 API 规范

### 健康检查端点

所有技术栈必须提供统一的健康检查 API：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 服务健康状态检查 |

**响应格式：**

```json
{
  "status": "healthy",
  "timestamp": "2025-05-19T10:00:00Z"
}
```

### API 文档

各技术栈提供标准 API 文档：

- **Python**: `/docs` (Swagger), `/redoc` (ReDoc)
- **Rust**: 需通过代码注释生成
- **Java**: `/swagger-ui.html` (规划)
- **.NET**: `/swagger` (规划)

### RESTful 规范

- URL 设计：资源导向，小写连字符分隔
- HTTP 方法：GET 查询、POST 创建、PUT 更新、DELETE 删除
- 响应格式：统一 JSON 结构，包含 `code`、`message`、`data` 字段

## 统一配置管理

### 配置文件结构

```
server/config/
├── application.yml           # 基础配置（提交）
├── application-local.yml.example # 本地配置示例（提交）
└── application-local.yml     # 本地配置（不提交）

server/{技术栈}/config/       # 引用共享配置
```

### 配置优先级

1. 环境变量覆盖（最高优先级）
2. 环境特定配置文件 `application-{env}.yml`
3. 基础配置文件 `application.yml`

### 环境选择

通过 `SERVICE_ENV` 环境变量指定运行环境：`local`、`dev`、`test`、`prod`

## 开发规范

### 代码质量

- 遵循各语言的社区规范和最佳实践
- 统一使用 Conventional Commits 提交规范
- 保持各技术栈 API 行为一致性

### 测试要求

- 单元测试覆盖核心业务逻辑
- 集成测试验证 API 行为
- 各技术栈使用对应测试框架

### 技术栈对应测试框架

| 技术栈 | 测试框架 |
|--------|----------|
| Python | pytest |
| Rust | cargo-nextest |
| Java | JUnit 5 (规划) |
| .NET | xUnit (规划) |

## 快速开始

1. 选择目标技术栈目录
2. 阅读对应 `CLAUDE.md` 开发指南
3. 按文档安装依赖并启动服务
4. 访问 `/health` 端点验证服务状态

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
