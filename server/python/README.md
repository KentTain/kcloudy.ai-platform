# Demo Backend

Demo AI 助手平台后端服务，基于 FastAPI 构建。

## 功能特点

### 核心能力

- **基于 FastAPI 的 Web 服务**：高性能异步 Web 框架
- **基于 langchain langgraph**：AI智能体 框架
- **统一返回结构**：RESTful API 设计，统一的 JSON 消息体格式
- **完善的错误处理**：全局异常处理和自动错误追踪

### 数据与存储

- **数据库集成**：SQLAlchemy 2.0 + Alembic + PostgreSQL (pgvector)
- **缓存支持**：Redis 用于高性能缓存
- **分层配置**：基于 YAML 的多环境配置系统

## 环境要求

- Python 3.12
- PostgreSQL 14+ (可选)
- Redis 6+ (可选)
- uv (Python 包管理器)

## 快速开始

### 安装

```bash
# 安装依赖
uv sync

# 初始化开发环境
uv run setup-dev

# 检查开发环境
uv run check-dev
```

### 配置

配置文件统一放置在 `server/config/` 目录下：

```bash
# 复制配置文件
cp server/config/application-local.yml.example server/config/application-local.yml

# 编辑配置文件，配置数据库和 Redis 连接
vim server/config/application-local.yml
```

### 运行

项目提供统一的管理脚本 `manage.py`：

```bash
# 启动 Web 服务器
uv run python manage.py runserver

# 指定主机/端口
uv run python manage.py runserver --host 0.0.0.0 --port 8080

# 启动开发模式（热重载）
uv run python manage.py runserver --reload

# 启动定时任务调度器
uv run python manage.py runtask

# 启动监听器服务
uv run python manage.py runlistener
```

也可以使用简化命令：

```bash
uv run runserver
uv run runserver --host 0.0.0.0 --port 8080
```

### 访问

- API 文档：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

## 开发指南

详细开发指南见 [CLAUDE.md](CLAUDE.md)。

### 代码风格

```bash
# 格式化代码
uv run format-code

# 仅检查
uv run format-code --check-only
```

### 数据库迁移

项目采用模块化迁移架构，支持多业务模块独立迁移和数据初始化。

```bash
# 查看迁移状态
uv run python manage.py db current

# 执行迁移
uv run python manage.py db migrate

# 预览迁移 SQL（不执行）
uv run python manage.py db migrate --sql

# 回退迁移
uv run python manage.py db downgrade

# 查看迁移历史
uv run python manage.py db history

# 创建新迁移
uv run python manage.py db makemigrations -m "描述"
```

### 数据初始化

```bash
# 初始化所有模块的默认数据
uv run python manage.py seed

# 预览待初始化的数据（不写入）
uv run python manage.py seed --dry-run

# 初始化指定模块
uv run python manage.py seed --module tenant
```

### 测试

详细测试说明见 [tests/README.md](tests/README.md)。

```bash
# 运行所有测试
uv run pytest

# 运行单元测试
uv run pytest tests/demo/unit/ -v

# 运行指定测试文件
uv run pytest tests/demo/unit/config/ -v

# 跳过慢测试
uv run pytest -m "not slow"
```

**测试标记：**

| 标记 | 说明 |
|------|------|
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.slow` | 慢测试 |
| `@pytest.mark.db` | 数据库测试 |
| `@pytest.mark.api` | API 测试 |

### MVC 架构

项目采用 Controller → Service → Model 三层架构：

- **Controller**：HTTP 路由和参数解析
- **Service**：业务逻辑和事务管理
- **Model**：ORM 模型和数据库操作

## 技术栈

- **后端框架**：FastAPI 0.115
- **ORM**：SQLAlchemy 2.0
- **数据库**：PostgreSQL + pgvector
- **缓存**：Redis
- **验证**：Pydantic 2.10
- **迁移工具**：Alembic 1.14
- **测试**：pytest + pytest-asyncio

## 项目结构

```text
server/python/
├── manage.py               # 统一管理脚本
├── src/demo/               # Demo 模块源码
│   ├── controllers/        # API 控制器
│   ├── services/           # 业务逻辑层
│   ├── models/             # 数据库模型
│   ├── schemas/            # Pydantic 模型
│   ├── configs/            # 配置管理
│   ├── migrations/         # 数据库迁移
│   └── seeds/              # 数据初始化脚本
├── tests/demo/             # Demo 模块测试
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── fixtures/           # 测试夹具
└── config/                 # 配置目录（引用共享配置）
```

## License

Copyright © 2025 Moles. All Rights Reserved.
