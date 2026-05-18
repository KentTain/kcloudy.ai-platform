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

```bash
# 复制配置文件
cp config/application-local.yml.example config/application-local.yml

# 编辑配置文件，配置数据库和 Redis 连接
vim config/application-local.yml
```

### 运行

```bash
# 启动 Web 服务器
uv run runserver

# 指定主机/端口
uv run runserver --host 0.0.0.0 --port 8080

# 启动开发模式（热重载）
uv run runserver --reload
```

### 访问

- API 文档：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

## 开发指南

### 代码风格

```bash
# 格式化代码
uv run format-code

# 仅检查
uv run format-code --check-only
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回退迁移
alembic downgrade -1
```

### 测试

详细测试说明见 [tests/README.md](tests/README.md) 和 [tests/CLAUDE.md](tests/CLAUDE.md)。

```bash
# 运行所有测试
uv run pytest

# 运行指定目录的测试
uv run pytest tests/unit/utils/ -v

# 运行指定测试文件
uv run pytest tests/unit/utils/test_dictionary_util.py

# 运行并显示打印输出
uv run pytest -s

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

**测试目录结构：**

```text
tests/
├── unit/           # 单元测试
│   ├── cache/      # Redis 缓存测试
│   ├── config/     # 配置管理测试
│   ├── model/      # Pydantic 模型测试
│   ├── serialization/  # 序列化测试
│   ├── services/   # 服务层测试
│   └── utils/      # 工具函数测试
├── fixtures/       # 测试夹具和数据
├── studies/        # 代码预研（非正式测试）
├── examples/       # 示例代码测试
├── conftest.py     # pytest 全局配置
├── README.md       # 测试说明文档
└── CLAUDE.md       # 测试规范文档
```

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
├── src/demo/              # 后端源码
│   ├── controllers/       # API 控制器
│   ├── services/          # 业务逻辑层
│   ├── models/            # 数据库模型
│   ├── schemas/           # Pydantic 模型
│   ├── configs/           # 配置管理
│   ├── common/            # 通用模块
│   ├── core/              # 核心框架
│   ├── utils/             # 工具函数
│   ├── examples/          # 示例代码
│   └── migrations/        # 数据库迁移
├── config/                # 配置文件
├── scripts/               # 开发脚本
└── tests/                 # 测试文件
```
