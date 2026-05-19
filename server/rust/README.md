# Demo - Rust 后端

最小化 AI 助手平台 Rust 后端实现，基于 Axum 框架构建的高性能异步 Web 服务。

## 技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| Web 框架 | Axum 0.8 | Tokio 官方出品，异步性能优异 |
| AI 编排 | LangChain Rust | 完善的 Chain、Agent 和工具链生态 |
| 数据库 | SQLx 0.8 | 编译期 SQL 检查，原生异步 |
| 缓存 | redis-rs 0.29 | 官方标准客户端 |
| 测试 | cargo-nextest | 新一代测试运行器 |

## 项目结构

```text
server/rust/
├── Cargo.toml              # 项目配置
├── src/
│   ├── main.rs             # 入口文件
│   └── demo/               # Demo 模块
│       ├── lib.rs          # 库入口
│       ├── config/         # 配置管理
│       ├── db/             # 数据库连接
│       ├── models/         # 数据库模型
│       ├── schemas/        # 数据校验模型
│       ├── services/       # 业务服务层
│       ├── controllers/    # API 控制器
│       ├── common/         # 通用模块
│       ├── utils/          # 工具函数
│       └── examples/       # 示例代码
├── tests/
│   ├── unit.rs             # 单元测试
│   └── fixtures/           # 测试数据
├── benches/                # 性能基准测试
└── config/                 # 配置目录（引用共享配置）
    └── README.md           # 配置说明
```

## 环境要求

- Rust 1.95+
- PostgreSQL 14+
- Redis 6+

## 快速开始

```bash
# 进入项目目录
cd server/rust

# 复制配置文件（配置统一放置在 server/config/）
cp server/config/application-local.yml.example server/config/application-local.yml

# 构建项目
cargo build

# 运行服务
cargo run

# 运行开发模式（带日志）
RUST_LOG=debug cargo run
```

## 开发命令

```bash
# 检查代码
cargo check

# 构建项目
cargo build

# 构建生产版本
cargo build --release

# 运行测试
cargo test

# 使用 nextest 运行测试
cargo nextest run

# 运行基准测试
cargo bench

# 生成文档
cargo doc --open

# 代码格式化
cargo fmt

# 代码检查
cargo clippy
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| GET | /api/v1/datasets | 获取知识库列表 |
| POST | /api/v1/datasets | 创建知识库 |
| GET | /api/v1/datasets/{id} | 获取知识库详情 |
| PUT | /api/v1/datasets/{id} | 更新知识库 |
| DELETE | /api/v1/datasets/{id} | 删除知识库 |

## 配置说明

配置文件统一放置在 `server/config/` 目录下：

```bash
server/config/
├── application.yml              # 基础配置
├── application-local.yml.example # 本地配置示例
└── application-local.yml        # 本地配置（不提交）
```

支持环境变量覆盖：

| 环境变量 | 说明 |
|----------|------|
| DEMO_SERVER__HOST | 服务器地址 |
| DEMO_SERVER__PORT | 服务器端口 |
| DEMO_DATABASE__URL | 数据库连接 URL |
| DEMO_REDIS__URL | Redis 连接 URL |

## License

Copyright © 2025 Moles. All Rights Reserved.
