# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在后端应用中工作时提供指导。

## 项目概述

Demo 是一个最小化 AI 助手平台演示项目后端，使用 FastAPI 构建。项目采用基于 uv 的 Python 单包结构。

**核心技术栈：**

- 框架：FastAPI, SQLAlchemy 2.0, Alembic
- AI框架：langchain 1.3.0, langgraph 1.2.0
- 数据库：PostgreSQL (pgvector), Redis
- 验证：Pydantic 2.10
- 测试：pytest, pytest-asyncio, pytest-mock

## 项目结构

```
server/python/                 # Python 后端项目根目录
├── src/demo/                  # 后端源码
│   ├── components/            # 可插拔组件框架
│   ├── controllers/           # API 控制器
│   ├── services/              # 业务逻辑层
│   ├── models/                # SQLAlchemy 数据库模型
│   ├── schemas/               # Pydantic 校验模型
│   ├── configs/               # 配置管理（基于 YAML）
│   ├── common/                # 通用模块（异常、上下文等）
│   ├── db/                    # 数据库引擎配置
│   ├── migrations/            # Alembic 数据库迁移文件
│   ├── core/                  # 核心框架（路径、环境、单例等）
│   ├── utils/                 # 工具函数
│   ├── examples/              # 示例代码（LangChain、MCP 等）
│   ├── application_web.py     # FastAPI 应用入口
│   ├── application_task.py    # 任务调度器入口
│   ├── application_listener.py # 消息监听器入口
│   └── run.py                 # Web 服务器启动入口
├── tests/                     # 测试文件
├── config/                    # 配置文件
│   ├── application.yml        # 基础配置
│   ├── application-local.yml.example  # 本地开发配置示例
│   └── application-local.yml  # 本地开发配置（不提交）
├── scripts/                   # 开发脚本
│   └── dev/
│       ├── setup_dev.py       # 开发环境初始化
│       ├── check_dev.py       # 开发环境检查
│       └── format_code.py     # 代码格式化
├── pyproject.toml             # 项目配置
├── alembic.ini                # Alembic 配置
├── pytest.ini                 # pytest 配置
└── .ruff.toml                 # Ruff 配置
```

## 开发命令

**后端入口为 `src/demo/run.py`，请始终从项目根目录 `server/python` 运行命令。**

```bash
# 安装依赖
uv sync

# 启动 Web 服务器
uv run runserver

# 指定主机/端口启动 Web 服务器
uv run runserver --host 0.0.0.0 --port 8080

# 启动开发模式（热重载）
uv run runserver --reload

# 启动调度服务（占位符）
uv run runtask

# 启动监听服务（占位符）
uv run runlistener

# 开发环境初始化
uv run setup-dev

# 开发环境检查
uv run check-dev

# 代码格式化和检查
uv run format-code
uv run format-code --check-only  # 仅检查，不修复

# 数据库迁移
alembic revision --autogenerate -m "描述"  # 创建迁移
alembic upgrade head                       # 应用迁移
alembic downgrade -1                       # 回退迁移

# 测试
uv run pytest                              # 运行所有测试
uv run pytest -v                           # 详细输出
uv run pytest -m "not slow"                # 跳过慢测试
uv run pytest tests/path/to/test_file.py   # 运行指定测试文件
```

## API 端点结构

平台提供多个 API 端点：

- **`/health`** - 健康检查
- **`/api/v1/datasets`** - 知识库 CRUD 示例
- **`/docs`** - Swagger API 文档
- **`/redoc`** - ReDoc API 文档

## 配置管理

采用 Spring Boot 风格的分层配置机制，配置文件为 YAML 格式。

**配置文件：**

- `config/application.yml` - 基础配置
- `config/application-{env}.yml` - 环境特定配置（local/dev/test/prod）

**环境选择：** 通过 `PYTHON_SERVICE_ENV` 环境变量指定，默认 `local`。

**配置优先级：** YAML 文件 → OS 环境变量覆盖。

## 代码质量标准

### Python

- **Linter/格式化工具**：Ruff
- **行宽**：88 个字符
- **Python 版本**：3.12
- **类型标注**：统一使用 `Mapped[...]` 声明式注解

### 提交规范

遵循 Conventional Commits 规范。

## 测试

测试框架使用 pytest，配置文件为项目根目录的 `pytest.ini`。详细测试说明见 [tests/README.md](tests/README.md) 和 [tests/CLAUDE.md](tests/CLAUDE.md)。

**测试目录结构：**

```text
tests/
├── unit/               # 单元测试
│   ├── cache/          # Redis 缓存测试
│   ├── config/         # 配置管理测试
│   ├── model/          # Pydantic 模型测试
│   ├── serialization/  # 序列化测试
│   ├── services/       # 服务层测试
│   └── utils/          # 工具函数测试
├── fixtures/           # 测试夹具和数据
├── studies/            # 代码预研（非正式测试）
├── examples/           # 示例代码测试
├── conftest.py         # pytest 全局配置
├── README.md           # 测试说明文档
└── CLAUDE.md           # 测试规范文档
```

**常用命令：**

```bash
uv run pytest                    # 运行所有测试
uv run pytest -v                 # 详细输出
uv run pytest -x                 # 遇到第一个失败即停止
uv run pytest -m "not slow"      # 跳过标记为 slow 的测试
uv run pytest -m "integration"   # 仅运行集成测试
```

**测试标记：**

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.slow` - 慢测试
- `@pytest.mark.db` - 数据库测试
- `@pytest.mark.api` - API 测试

## MVC 编码模式

平台采用 Controller → Service → Model 三层架构。

### Controller 层

- **职责**：HTTP 请求路由，参数解析，调用 Service 层，返回响应
- **响应封装**：使用 `ORJSONResponse` 返回统一格式的 JSON 响应
- **数据转换**：通过 `Vo.model_validate()` 将 Model 转换为 VO

### Service 层

- **职责**：核心业务逻辑，数据库操作、事务管理
- **组织形式**：每个 Service 为一个类，模块底部实例化为单例
- **事务管理**：在 `try/except` 中执行，成功 `commit()`，异常 `rollback()`

### Model 层

- **ORM 基类**：继承 `BaseModel` + 所需的 Mixin
- **字段声明**：统一使用 `Mapped[type] = mapped_column(...)` 声明式注解

## 环境要求

- Python 3.12
- PostgreSQL 14+ (可选，用于数据库功能)
- Redis 6+ (可选，用于缓存功能)
- uv (Python 包管理器)

## 快速开始

1. 安装依赖：`uv sync`
2. 复制配置：`cp config/application-local.yml.example config/application-local.yml`
3. 启动服务：`uv run runserver`
4. 访问文档：http://localhost:8000/docs
