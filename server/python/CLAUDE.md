# CLAUDE.md

本文件为 Claude Code 在 Python 后端项目中工作时提供指导。

## 项目概述

Python 后端使用 FastAPI + SQLAlchemy 2.0 构建，提供 AI 助手平台演示。项目采用基于 uv 的单包结构，支持 MVC 分层架构。

**核心技术栈：**

- 框架：FastAPI, SQLAlchemy 2.0, Alembic
- AI框架：langchain 1.3.0, langgraph 1.2.0
- 数据库：PostgreSQL (pgvector), Redis
- 验证：Pydantic 2.10
- 测试：pytest, pytest-asyncio, pytest-mock

## 项目结构

```text
server/python/
├── src/                       # 源码目录
│   ├── demo/                  # Demo 业务模块
│   └── framework/             # 基础设施框架
├── tests/                     # 测试目录
│   ├── demo/                  # Demo 模块测试
│   └── framework/             # Framework 模块测试
├── config/                    # 配置目录（符号链接到 server/config/）
├── scripts/                   # 开发脚本
├── pyproject.toml             # 项目配置
├── alembic.ini                # Alembic 配置
├── pytest.ini                 # pytest 配置
└── .ruff.toml                 # Ruff 配置
```

## 功能模块

| 模块 | 说明 | 详细文档 |
|------|------|----------|
| demo | 业务演示模块：API 控制器、服务层、数据模型 | [src/CLAUDE.md](src/CLAUDE.md) |
| framework | 基础设施：配置、缓存、存储、队列、锁、租户 | [src/CLAUDE.md](src/CLAUDE.md) |

## 开发命令

```bash
# 安装依赖
uv sync

# 启动 Web 服务器
uv run runserver

# 指定主机/端口启动
uv run runserver --host 0.0.0.0 --port 8080

# 开发模式（热重载）
uv run runserver --reload

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic downgrade -1

# 测试
uv run pytest
uv run pytest -v
uv run pytest tests/demo/unit/
```

## 配置管理

采用 Spring Boot 风格的分层配置，配置文件统一在 `server/config/` 目录。

```bash
# 本地开发配置
cp server/config/application-local.yml.example server/config/application-local.yml
```

**环境选择：** 通过 `PYTHON_SERVICE_ENV` 环境变量指定，默认 `local`。

## 代码质量标准

- **Linter/格式化**：Ruff
- **行宽**：88 字符
- **Python 版本**：3.12
- **类型标注**：统一使用 `Mapped[...]` 声明式注解

## 详细文档

- **开发指南**：[src/CLAUDE.md](src/CLAUDE.md)
- **测试指南**：[tests/CLAUDE.md](tests/CLAUDE.md)

## 环境要求

- Python 3.12+
- PostgreSQL 14+
- Redis 6+
- uv (Python 包管理器)

## License

Copyright © 2025 Moles. All Rights Reserved.
