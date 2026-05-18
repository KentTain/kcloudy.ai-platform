# 后端服务

本目录包含多种后端技术实现，每种技术作为独立子项目存在。

## 目录结构

```
server/
├── python/     # Python 后端（FastAPI）✅ 可用
├── rust/       # Rust 后端（Axum）✅ 可用
├── java/       # Java 后端（Spring Boot）🚧 规划中
└── netcore/    # .NET 后端 🚧 规划中
```

## 环境安装指南

### Python 后端

**环境要求：** Python 3.12+ / uv

#### 安装 uv（推荐）

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 安装 Python

```bash
# 使用 uv 安装 Python 3.12
uv python install 3.12

# 验证安装
uv python list
```

#### 启动项目

```bash
cd server/python

# 安装依赖
uv sync

# 启动服务
uv run runserver
```

详细文档：[python/CLAUDE.md](python/CLAUDE.md)

---

### Rust 后端

**环境要求：** Rust 1.75+ / Cargo

#### 安装 Rust（推荐使用 rustup）

```bash
# Windows (PowerShell)
# 下载并运行 rustup-init.exe
# 或访问 https://rustup.rs/

# macOS / Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

#### 安装指定版本

```bash
# 安装 stable 版本
rustup install stable

# 安装指定版本（如 1.85）
rustup install 1.85

# 设置默认版本
rustup default stable

# 验证安装
rustc --version
cargo --version
```

#### 安装常用组件

```bash
# 安装 rust-analyzer（LSP）
rustup component add rust-analyzer

# 安装 clippy（Linter）
rustup component add clippy

# 安装 rustfmt（格式化）
rustup component add rustfmt

# 安装 rust-src（源码，用于 IDE）
rustup component add rust-src
```

#### 安装 cargo-nextest（测试运行器）

```bash
cargo install cargo-nextest
```

#### 配置国内镜像（可选）

编辑 `~/.cargo/config.toml`：

```toml
[source.crates-io]
replace-with = "ustc"

[source.ustc]
registry = "https://mirrors.ustc.edu.cn/crates.io-index"
```

#### 启动项目

```bash
cd server/rust

# 构建项目
cargo build

# 启动服务
cargo run
```

详细文档：[rust/CLAUDE.md](rust/CLAUDE.md)

---

### Java 后端（规划中）

**环境要求：** Java 21+ / Maven

#### 安装 JDK 21

```bash
# Windows (使用 scoop)
scoop install openjdk21

# macOS (使用 Homebrew)
brew install openjdk@21

# Ubuntu/Debian
sudo apt install openjdk-21-jdk

# 验证安装
java -version
```

#### 安装 Maven

```bash
# Windows (使用 scoop)
scoop install maven

# macOS (使用 Homebrew)
brew install maven

# Ubuntu/Debian
sudo apt install maven

# 验证安装
mvn -version
```

---

## 公共依赖

### PostgreSQL

所有后端项目共享同一个 PostgreSQL 数据库。

```bash
# Windows (使用 scoop)
scoop install postgresql

# macOS (使用 Homebrew)
brew install postgresql@14

# Ubuntu/Debian
sudo apt install postgresql-14

# 创建数据库
createdb demo

# 验证连接
psql -d demo
```

### Redis

所有后端项目共享同一个 Redis 缓存。

```bash
# Windows (使用 scoop)
scoop install redis

# macOS (使用 Homebrew)
brew install redis

# Ubuntu/Debian
sudo apt install redis-server

# 启动服务
redis-server

# 验证连接
redis-cli ping
```

## 开发工具推荐

### VS Code 扩展

- **Python:** ms-python.python, charliermarsh.ruff
- **Rust:** rust-lang.rust-analyzer, vadimcn.vscode-lldb, serayuzgur.crates
- **通用:** tamasfe.even-better-toml, redhat.vscode-yaml

完整列表见项目根目录 `.vscode/extensions.json`。

## License

Copyright © 2025 Moles. All Rights Reserved.
