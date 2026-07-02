# Python 后端测试说明

## 测试目录结构

```text
tests/
├── conftest.py                # 根级别配置：统一配置和通用 fixtures
│
├── ai/                        # AI 模块测试
│   ├── conftest.py            # AI 模块独有配置：API Key、测试数据、Mock fixtures
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── e2e/                   # E2E 测试
│       └── conftest.py        # E2E 独有配置：pytest 标记、插件测试 fixtures
│
├── demo/                      # Demo 模块测试
│   ├── fixtures/              # 测试夹具和数据
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   ├── examples/              # 示例代码测试
│   └── studies/               # 代码预研
│
├── framework/                 # Framework 模块测试
│   ├── fixtures/              # 测试夹具
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
│
├── iam/                       # IAM 模块测试
│   ├── conftest.py            # IAM 模块独有配置：测试租户、用户清理
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
│
└── tenant/                    # Tenant 模块测试
    ├── conftest.py            # Tenant 模块独有配置：Mock 插件存储服务
    └── unit/                  # 单元测试
```

## conftest.py 层级结构

测试配置采用**两级结构**，避免重复配置：

### 根级别配置（tests/conftest.py）

提供所有模块共享的配置和 fixtures：

| 配置类别 | 说明 |
| --- | --- |
| **环境变量** | `PYTHON_SERVICE_ENV=local`、`TZ=Asia/Shanghai` |
| **Windows 事件循环** | 使用 `WindowsSelectorEventLoopPolicy` 解决 pytest-asyncio 兼容性问题 |
| **日志配置** | 配置 SQLAlchemy、Alembic 等日志级别 |
| **LangChain 依赖检测** | 自动跳过 LangChain 相关测试（当依赖缺失时） |
| **配置加载** | `integration_settings` fixture 加载 `server/config/application-local.yml` |
| **服务可用性检测** | `redis_available`、`postgres_available`、`minio_available` |
| **数据库 fixtures** | `postgres_engine`、`postgres_session` |
| **Redis fixtures** | `redis_client`、`redis_key_prefix`、`redis_cleanup` |
| **MinIO fixtures** | `minio_client`、`minio_test_bucket`、`minio_cleanup` |
| **工具函数** | `unique_id()`、`wait_for_condition()` |
| **单元测试 fixtures** | `mock_session`（模拟数据库会话） |

### 模块级别配置（tests/{module}/conftest.py）

提供模块独有的 fixtures：

| 模块 | 独有 fixtures |
| --- | --- |
| `ai/` | `ai_settings`、`test_tenant_id`、`test_user_id`、API Key fixtures、Mock 数据 fixtures |
| `ai/e2e/` | `e2e_engine`、`e2e_session`、`plugin_package_path`、`plugin_runtime_setup`、pytest e2e 标记配置 |
| `iam/` | `test_tenant_id`、`ensure_test_tenant`、`cleanup_users` |
| `tenant/` | `mock_plugin_storage_service` |

### 配置原则

1. **子目录不再单独配置**：`unit/`、`integration/`、`e2e/` 子目录不再有独立的 conftest.py
2. **统一配置集中**：环境变量、事件循环、服务检测等统一配置集中在根 conftest.py
3. **模块独有配置下沉**：测试数据、模块特有 fixtures 放在模块根目录 conftest.py

## 测试类型

| 类型 | 说明 | 特点 |
| --- | --- | --- |
| **单元测试** | 使用 mock 隔离外部依赖，验证函数、类、Service 逻辑 | 快速、无外部依赖 |
| **集成测试** | 依赖真实 Redis、PostgreSQL、MinIO，测试跨组件协作 | 需服务可用、可跳过、可清理 |
| **E2E 测试** | 端到端测试，验证完整业务流程 | 默认跳过，需 `-m e2e` 运行 |
| **示例测试** | 验证 AI 示例代码可导入运行 | LangChain 依赖缺失时自动跳过 |
| **代码预研** | 技术探索验证 | 不作为正式功能测试依据 |

## 运行测试

### 基本命令

```bash
# 全部测试
uv run pytest

# 详细输出
uv run pytest -v

# 遇到第一个失败即停止
uv run pytest -x

# 显示打印输出
uv run pytest -s
```

### 按模块运行

```bash
uv run pytest tests/demo/ -v
uv run pytest tests/framework/ -v
uv run pytest tests/ai/ -v
uv run pytest tests/iam/ -v
uv run pytest tests/tenant/ -v
```

### 按类型运行

```bash
# 单元测试
uv run pytest tests/demo/unit/ -v
uv run pytest tests/framework/unit/ -v

# 集成测试
uv run pytest tests/framework/integration/ -v
uv run pytest tests/ai/integration/ -v

# E2E 测试（需显式指定 -m e2e）
uv run pytest -m e2e tests/ai/e2e/ -v
```

### 按标记运行

```bash
uv run pytest -m unit          # 只运行单元测试
uv run pytest -m integration   # 只运行集成测试
uv run pytest -m e2e           # 只运行 E2E 测试
uv run pytest -m "not slow"    # 跳过慢测试
```

## 测试标记

| 标记 | 说明 | 使用场景 |
| --- | --- | --- |
| `@pytest.mark.unit` | 单元测试 | 隔离依赖的快速测试 |
| `@pytest.mark.integration` | 集成测试 | 需要真实外部服务的测试 |
| `@pytest.mark.e2e` | E2E 测试 | 端到端测试，默认跳过 |
| `@pytest.mark.slow` | 慢测试 | 执行时间较长的测试 |
| `@pytest.mark.db` | 数据库测试 | 需要数据库的测试 |
| `@pytest.mark.api` | API 测试 | 测试 API 端点 |
| `@pytest.mark.asyncio` | 异步测试 | 测试异步代码 |

## 通用 fixtures 使用示例

### 数据库测试

```python
import pytest
from sqlalchemy import select
from myapp.models import User


@pytest.mark.asyncio
async def test_database(postgres_session):
    """使用 PostgreSQL 会话测试"""
    # 创建测试数据
    user = User(username="test")
    postgres_session.add(user)
    await postgres_session.commit()

    # 查询验证
    result = await postgres_session.execute(select(User))
    users = result.scalars().all()
    assert len(users) == 1
```

### Redis 测试

```python
import pytest


@pytest.mark.asyncio
async def test_redis(redis_client, redis_key_prefix):
    """使用 Redis 客户端测试"""
    key = f"{redis_key_prefix}test_key"
    await redis_client.set(key, "test_value")

    value = await redis_client.get(key)
    assert value == "test_value"

    # 自动清理：redis_cleanup fixture 会清理带有前缀的键
```

### 单元测试（Mock Session）

```python
import pytest
from myapp.services import UserService


@pytest.mark.asyncio
async def test_user_service(mock_session):
    """使用 Mock Session 测试 Service"""
    service = UserService()

    # 配置 mock 行为
    mock_session.scalar_one_or_none.return_value = None

    # 执行测试
    result = await service.get_by_id("test-id")
    assert result is None
```

### 服务可用性检测

```python
import pytest


@pytest.mark.asyncio
async def test_with_service_check(redis_available, redis_client):
    """依赖服务可用性的测试"""
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    # 测试逻辑...
```

## 编写测试规则

### 基本原则

- **测试路径对应源码路径**：`tests/framework/unit/cache/` 对应 `src/framework/cache/`
- **单元测试隔离依赖**：不访问真实网络、数据库、Redis 或对象存储
- **集成测试检测服务**：必须检测依赖服务可用性，不可用时跳过
- **测试数据分离**：放在 `fixtures/` 目录，避免内联大段 JSON 或二进制内容
- **异步测试标记**：使用 `@pytest.mark.asyncio`

### Bug 修复流程

1. 先补充能复现问题的测试
2. 运行测试确认失败
3. 修改实现代码
4. 运行测试确认通过

### 新增模块流程

1. 创建 `tests/{module}/` 目录
2. 如有模块独有 fixtures，创建 `tests/{module}/conftest.py`
3. 创建 `unit/`、`integration/` 子目录
4. 必要时补充模块级 `CLAUDE.md`

## pytest 配置文件

pytest 配置在 `server/python/pyproject.toml` 中：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
filterwarnings = [
    "ignore::DeprecationWarning",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests",
    "db: Database tests",
    "api: API tests",
]
```

## 开发指南

详细开发指南见上级目录的 [CLAUDE.md](../CLAUDE.md)。
