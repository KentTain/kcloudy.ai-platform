# Rust 后端指南

本文件为 Claude Code 在 Rust 后端项目中工作时提供指导。

## 项目定位

Rust 后端使用 Axum 框架构建，是 AI Platform 的 Rust 技术栈实现。项目采用 Rust 异步生态，提供高性能的 Web 服务。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Axum 0.8, Tower, Tokio |
| AI 框架 | LangChain Rust |
| 数据库 | SQLx 0.8 (PostgreSQL + pgvector) |
| 缓存 | redis-rs 0.29 |
| 测试 | cargo-nextest, axum-test, mockall |

## 模块导航

| 模块 | 定位 | 详细文档 |
|------|------|----------|
| demo | 业务演示模块 | [src/demo/](src/demo/) |

## 架构规则

| 规则 | 说明 |
|------|------|
| 分层架构 | Controller → Service → Model |
| 响应格式 | 使用 `ApiResponse<T>` 返回统一 JSON |

## 核心命令

```bash
# 构建项目
cargo build

# 运行服务
cargo run
RUST_LOG=debug cargo run

# 运行测试
cargo test
cargo nextest run

# 代码检查
cargo fmt
cargo clippy
```

## 开发约束

- Rust 版本：1.95+
- 行宽：100 字符
- 格式化：rustfmt
- Linter：clippy

## 环境要求

- Rust 1.95+
- PostgreSQL 14+
- Redis 6+

详细使用示例见 [README.md](README.md)。
