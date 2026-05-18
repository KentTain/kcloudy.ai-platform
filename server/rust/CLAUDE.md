# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在 Rust 后端项目中工作时提供指导。

## 项目概述

Demo 是一个最小化 AI 助手平台演示项目后端，使用 Axum 框架构建。项目采用 Rust 异步生态，提供高性能的 Web 服务。

**核心技术栈：**

- 框架：Axum 0.8, Tower, Tokio
- AI框架：LangChain Rust
- 数据库：SQLx 0.8 (PostgreSQL + pgvector)
- 缓存：redis-rs 0.29
- 测试：cargo-nextest, axum-test, mockall, Criterion

## 项目结构

```text
server/rust/                 # Rust 后端项目根目录
├── src/                     # 源代码
│   ├── main.rs              # 主入口
│   ├── lib.rs               # 库入口
│   ├── config/              # 配置管理
│   │   ├── mod.rs           # 模块入口
│   │   └── settings.rs      # 配置定义
│   ├── db/                  # 数据库层
│   │   ├── mod.rs           # 模块入口
│   │   └── pool.rs          # 连接池管理
│   ├── models/              # 数据库模型
│   │   ├── mod.rs           # 基础模型和 Mixins
│   │   └── dataset.rs       # Dataset 模型
│   ├── schemas/             # 数据校验模型
│   │   ├── mod.rs           # 公共 schemas
│   │   └── dataset.rs       # Dataset schemas
│   ├── services/            # 业务服务层
│   │   ├── mod.rs           # 模块入口
│   │   └── dataset.rs       # Dataset 服务
│   ├── controllers/         # API 控制器
│   │   ├── mod.rs           # 应用工厂
│   │   ├── health.rs        # 健康检查
│   │   └── dataset.rs       # Dataset API
│   ├── common/              # 通用模块
│   │   ├── mod.rs           # 模块入口
│   │   ├── error.rs         # 错误处理
│   │   └── context.rs       # 请求上下文
│   └── utils/               # 工具函数
│       ├── mod.rs           # 模块入口
│       └── cache.rs         # Redis 缓存
├── tests/                   # 测试文件
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   └── fixtures/            # 测试数据
├── benches/                 # 性能基准测试
├── config/                  # 配置文件
│   ├── application.yml      # 基础配置
│   └── application-local.yml.example  # 本地配置示例
├── Cargo.toml               # 项目配置
└── .nextest.toml            # Nextest 配置
```

## 开发命令

```bash
# 构建项目
cargo build

# 运行服务
cargo run

# 运行开发模式
RUST_LOG=debug cargo run

# 指定配置文件
cargo run -- --config config/application-local.yml

# 运行测试
cargo test

# 使用 nextest 运行测试（推荐）
cargo nextest run

# 运行基准测试
cargo bench

# 代码格式化
cargo fmt

# 代码检查
cargo clippy

# 生成文档
cargo doc --open
```

## API 端点结构

平台提供多个 API 端点：

- **`GET /health`** - 健康检查
- **`GET /api/v1/datasets`** - 获取知识库列表
- **`POST /api/v1/datasets`** - 创建知识库
- **`GET /api/v1/datasets/{id}`** - 获取知识库详情
- **`PUT /api/v1/datasets/{id}`** - 更新知识库
- **`DELETE /api/v1/datasets/{id}`** - 删除知识库

## 配置管理

采用 YAML 配置文件 + 环境变量覆盖机制。

**配置文件：**

- `config/application.yml` - 基础配置
- `config/application-{env}.yml` - 环境特定配置（未实现）

**环境变量覆盖：**

使用 `DEMO__` 前缀，双层下划线分隔：

```bash
DEMO__SERVER__PORT=9000
DEMO__DATABASE__URL=postgresql://...
DEMO__REDIS__URL=redis://...
```

## 代码质量标准

### Rust

- **格式化工具**：rustfmt
- **Linter**：clippy
- **最大行宽**：100 个字符
- **Rust 版本**：1.75+

### 提交规范

遵循 Conventional Commits 规范。

## 测试

测试框架使用 cargo-nextest，配置文件为 `.nextest.toml`。

**测试目录结构：**

```text
tests/
├── unit/               # 单元测试
│   ├── config.rs       # 配置测试
│   ├── error.rs        # 错误处理测试
│   └── cache.rs        # 缓存测试
├── integration/        # 集成测试
│   ├── common/         # 测试工具
│   └── fixtures/       # 测试数据
└── fixtures/           # 共享测试数据
```

**常用命令：**

```bash
cargo nextest run                    # 运行所有测试
cargo nextest run -v                 # 详细输出
cargo nextest run test_config        # 运行特定测试
cargo nextest run --profile ci       # CI 配置运行
```

## MVC 编码模式

平台采用 Controller → Service → Model 三层架构。

### Controller 层

- **职责**：HTTP 请求路由，参数解析，调用 Service 层，返回响应
- **响应封装**：使用 `ApiResponse<T>` 返回统一格式的 JSON 响应
- **数据转换**：通过 `DatasetVo::from(model)` 将 Model 转换为 VO

### Service 层

- **职责**：核心业务逻辑，数据库操作
- **组织形式**：每个 Service 为一个结构体，包含数据库连接引用
- **错误处理**：使用 `Result<T>` 返回结果

### Model 层

- **ORM 风格**：使用 SQLx 的 `query_as!` 宏进行类型安全查询
- **字段声明**：使用 `FromRow` derive 宏自动映射

## 环境要求

- Rust 1.75+
- PostgreSQL 14+ (可选，用于数据库功能)
- Redis 6+ (可选，用于缓存功能)

## 快速开始

1. 安装 Rust：`rustup install stable`
2. 复制配置：`cp config/application-local.yml.example config/application-local.yml`
3. 启动服务：`cargo run`
4. 访问健康检查：<http://localhost:8000/health>
