# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在项目中工作时提供指导。

## 项目概述

InitProject 是一个多技术栈的 AI 助手平台演示项目，提供多种后端和前端技术选型。项目采用模块化结构，每个技术栈作为独立子项目存在。

**核心目标：** 提供可对比、可学习的多技术栈实现参考。

## 项目结构

```text
init_project/
├── server/                    # 后端服务
│   ├── python/                # Python 后端（FastAPI）
│   ├── java/                  # Java 后端（Spring Boot）
│   ├── netcore/               # netcore 后端（DotNet Core）
│   └── rust/                  # Rust 后端（Axum）
├── web/                       # 前端 PC 项目
│   ├── vue/                   # Vue 3 + TypeScript
│   └── react/                 # React + TypeScript
├── app/                       # 前端 Mobile 项目
├── docker/                    # Docker 部署配置
└── docs/                      # 项目文档
```

## 技术选型

### 后端服务 (server/)

| 目录 | 语言 | 框架 | 状态 |
|------|------|------|------|
| server/python | Python 3.12 | FastAPI + SQLAlchemy 2.0 | ✅ 可用 |
| server/java | Java 21 | Spring Boot 3.x + MyBatis + LangChain4j | 🚧 规划中 |
| server/netcore | DotNet Core 8.0 | AspNetCore + EntityFrameworkCore + LangChain.NET | 🚧 规划中 |
| server/rust | Rust 1.75+ | Axum + SQLx + LangChainRust | ✅ 可用 |

### 前端 PC 项目 (web/)

| 目录 | 框架 | 语言 | 状态 |
|------|------|------|------|
| web/vue | Vue 3.5 | TypeScript 5.x | ✅ 可用 |
| web/react | React 19 | TypeScript 5.x | 🚧 规划中 |

### 前端 Mobile 项目 (app/)

| 目录 | 框架 | 语言 | 状态 |
|------|------|------|------|
| app/flutter | Flutter 3.x | Dart | 🚧 规划中 |
| app/react-native | React Native 0.7x | TypeScript | 🚧 规划中 |

## 子项目文档

每个子项目都有独立的 CLAUDE.md 文件，提供详细的技术指导：

- **Python 后端**: [server/python/CLAUDE.md](server/python/CLAUDE.md)
- **Vue 前端**: [web/vue/CLAUDE.md](web/vue/CLAUDE.md)
- **Java 后端**: [server/java/CLAUDE.md](server/java/CLAUDE.md) (规划中)
- **DotNet 后端**: [server/netcore/CLAUDE.md](server/netcore/CLAUDE.md) (规划中)
- **Rust 后端**: [server/rust/CLAUDE.md](server/rust/CLAUDE.md)

## 开发指南

### Python 后端

```bash
cd server/python

# 安装依赖
uv sync

# 启动服务
uv run runserver

# 运行测试
uv run pytest
```

详细文档：[server/python/CLAUDE.md](server/python/CLAUDE.md)

**测试说明：** [server/python/tests/README.md](server/python/tests/README.md)

### Rust 后端

```bash
cd server/rust

# 构建项目
cargo build

# 启动服务
cargo run

# 运行测试
cargo nextest run

# 运行基准测试
cargo bench
```

详细文档：[server/rust/CLAUDE.md](server/rust/CLAUDE.md)

### Vue 前端

```bash
cd web/vue

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 运行测试
pnpm test:unit -- --run
```

详细文档：[web/vue/CLAUDE.md](web/vue/CLAUDE.md)

### 配置管理

各子项目采用独立的配置管理：

- Python 后端：基于 YAML 的分层配置（`config/application.yml`）
- Rust 后端：基于 YAML 的配置 + 环境变量覆盖
- 配置优先级：YAML 文件 → 环境变量覆盖

### API 设计规范

所有后端实现遵循统一的 API 设计：

- **RESTful 风格**：资源导向的 URL 设计
- **统一响应格式**：标准化的 JSON 响应结构
- **错误处理**：全局异常处理和错误追踪

## 环境要求

### 后端

- Python 3.12+ / uv
- Java 21+ / Maven（规划中）
- Netcore 8.0+ / nuget（规划中）
- Rust 1.75+ / Cargo
- PostgreSQL 14+
- Redis 6+

### 前端

- Node.js 22+
- pnpm 10+

## 快速开始

1. 选择要使用的技术栈目录
2. 查看对应目录下的 README.md 和 CLAUDE.md
3. 按照文档说明安装依赖和启动服务

## License

Copyright © 2025 Moles. All Rights Reserved.
