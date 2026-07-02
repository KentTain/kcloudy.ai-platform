# Python 后端测试指南

本文件为 Claude Code 在 `server/python/tests/` 测试目录中工作时提供指导。

## 目录定位

`tests/` 按源码模块组织测试。模块测试目录与 `src/{module}/` 对齐：

| 测试目录 | 对应源码 | 详细文档 |
| --- | --- | --- |
| `ai/` | `src/ai/` | [ai/CLAUDE.md](ai/CLAUDE.md) |
| `demo/` | `src/demo/` | [demo/CLAUDE.md](demo/CLAUDE.md) |
| `framework/` | `src/framework/` | [framework/CLAUDE.md](framework/CLAUDE.md) |
| `iam/` | `src/iam/` | — |
| `tenant/` | `src/tenant/` | — |

## conftest.py 层级结构

测试配置采用两级结构：

| 层级 | 文件位置 | 职责 |
| --- | --- | --- |
| **根级别** | `tests/conftest.py` | 统一配置：环境变量、事件循环、日志、服务检测、通用 fixtures |
| **模块级别** | `tests/{module}/conftest.py` | 模块独有配置：测试数据、模块特有 fixtures |

**原则**：
- 子目录（unit/integration/e2e）不再单独配置 conftest.py
- 统一配置集中在根 conftest.py
- 模块独有配置放在模块根目录 conftest.py

## 通用运行命令

```bash
# 全部测试
uv run pytest

# 详细输出
uv run pytest -v

# 遇到第一个失败即停止
uv run pytest -x

# 跳过慢测试
uv run pytest -m "not slow"
```

按模块运行：

```bash
uv run pytest tests/demo/ -v
uv run pytest tests/framework/ -v
uv run pytest tests/ai/ -v
uv run pytest tests/iam/ -v
uv run pytest tests/tenant/ -v
```

e2e 测试运行方式：

```bash
# 显示跳过原因（推荐）
uv run pytest -v -rs tests/ai/e2e/

# 显示所有跳过原因的详细信息
uv run pytest -v -rs -s tests/ai/e2e/

# 完整输出（包括 traceback）
uv run pytest -v --tb=short tests/ai/e2e/
```

## 测试类型

| 类型 | 目录 | 约定 |
| --- | --- | --- |
| 单元测试 | `tests/{module}/unit/` | 使用 mock 或测试替身隔离外部依赖，验证函数、类和 Service 逻辑 |
| 集成测试 | `tests/{module}/integration/` | 使用真实 Redis、PostgreSQL、MinIO 或跨组件协作，必须可跳过、可清理 |
| E2E 测试 | `tests/{module}/e2e/` | 端到端测试，需显式指定 `-m e2e` 运行 |
| 示例测试 | `tests/demo/examples/` | 验证 AI 示例代码可导入、可运行关键路径 |
| 预研测试 | `tests/demo/studies/` | 技术探索，不作为正式功能验证的唯一依据 |
| 夹具 | `tests/{module}/fixtures/` | 测试数据、文件资源、辅助函数 |

## pytest 标记

| 标记 | 说明 |
| --- | --- |
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.e2e` | E2E 测试（默认跳过，需 `-m e2e` 运行） |
| `@pytest.mark.slow` | 慢测试 |
| `@pytest.mark.db` | 数据库测试 |
| `@pytest.mark.api` | API 测试 |
| `@pytest.mark.asyncio` | 异步测试 |

## 通用 fixtures（根 conftest.py 提供）

| Fixture | 说明 | 作用域 |
| --- | --- | --- |
| `integration_settings` | 加载集成测试配置 | session |
| `redis_available` | 检测 Redis 服务可用性 | session |
| `postgres_available` | 检测 PostgreSQL 服务可用性 | session |
| `minio_available` | 检测 MinIO 服务可用性 | session |
| `postgres_engine` | PostgreSQL 异步引擎 | function |
| `postgres_session` | PostgreSQL 异步会话 | function |
| `redis_client` | Redis 客户端 | function |
| `redis_key_prefix` | Redis 键前缀（测试隔离） | function |
| `redis_cleanup` | Redis 测试数据清理 | function |
| `minio_client` | MinIO 客户端 | function |
| `minio_test_bucket` | MinIO 测试存储桶名称 | function |
| `minio_cleanup` | MinIO 测试数据清理 | function |
| `init_redis` | 初始化 Redis 连接 | function |
| `mock_session` | 模拟数据库会话（单元测试） | function |

模块专属 fixtures 见对应模块测试文档。

## 模块级 fixtures 示例

### AI 模块 fixtures（tests/ai/conftest.py）

AI 模块提供 API Key 可用性检测 fixtures，用于 E2E 测试：

| Fixture | 说明 | 作用域 |
|---------|------|--------|
| `tongyi_api_key_available` | 检测通义千问 API Key 是否可用 | session |
| `gpustack_api_key_available` | 检测 GPUStack API Key 是否可用 | session |
| `tongyi_api_key` | 获取通义千问 API Key | function |
| `gpustack_api_key` | 获取 GPUStack API Key | function |
| `gpustack_endpoint` | 获取 GPUStack Endpoint | function |

**API Key 检测原理**：

- `tongyi_api_key_available`：向通义千问 API 发送测试请求，验证返回状态
- `gpustack_api_key_available`：向 GPUStack `/v1/models` 端点发送 GET 请求验证

**环境变量配置**：

```bash
# 可选：配置自定义 API Key（默认使用内置测试 Key）
export E2E_TONGYI_API_KEY="your-api-key"
export E2E_GPUSTACK_API_KEY="your-api-key"
export E2E_GPUSTACK_ENDPOINT="https://your-endpoint"
```

## 编写测试规则

- 测试路径应反映被测模块和能力，例如 `tests/framework/unit/cache/` 对应 `src/framework/cache/`。
- 单元测试不要访问真实网络、数据库、Redis 或对象存储。
- 集成测试必须检测依赖服务可用性；不可用时跳过相关测试。
- 测试数据应放在 `fixtures/`，避免在测试函数中内联大段 JSON 或二进制内容。
- 异步代码使用 `@pytest.mark.asyncio`。
- 修复 bug 时先补充能复现问题的测试，再修改实现。
- 新增模块时同步新增 `tests/{module}/`，必要时补充模块级 `CLAUDE.md`。

## 分层测试规范

不同层的测试关注点不同，应遵循各自的测试规范：

### Controller 层测试

**核心目标**：
1. Mock Service 层返回对象
2. 测试 Controller 的最终返回对象是否正确、是否出错

**测试关注点**：
- ✅ Service 返回数据后，Controller 正确封装响应
- ✅ Service 抛出异常或返回 None 时，Controller 正确处理错误
- ✅ 返回的 JSON 结构、字段名称、状态码是否正确
- ❌ 不验证 Service 方法被调用几次、调用参数是什么
- ❌ 不验证副作用方法是否被调用（除非影响返回结果）

**Mock 对象设置原则**：
- 只设置 Controller 真正用到的字段
- 避免设置无关属性导致测试冗余

详细规范和示例见 **[Controller 测试规范](CONTROLLER_TEST_GUIDE.md)**。

### Service 层测试

**核心目标**：
1. 测试业务逻辑正确性
2. 测试事务边界处理
3. 测试跨模型协作

**测试关注点**：
- ✅ 业务规则验证是否正确
- ✅ 数据库事务是否正确提交/回滚
- ✅ 跨模型操作是否正确协调
- ✅ 异常情况是否正确处理
- ❌ 不依赖真实数据库（使用 mock session 或测试数据库）
- ❌ 不测试 Controller 层的 HTTP 处理逻辑

### Model 层测试

**核心目标**：
1. 测试数据模型定义
2. 测试约束和验证规则
3. 测试模型方法

**测试关注点**：
- ✅ 字段类型和约束是否正确定义
- ✅ 模型方法（如 `to_dict()`）是否正确
- ✅ 关联关系是否正确定义
- ❌ 不测试 ORM 框架本身的功能

### 测试隔离原则

| 层级 | 依赖隔离 | Mock 对象 |
|------|---------|----------|
| Controller | Mock Service 层 | Service 返回对象 |
| Service | Mock 数据库层 | 数据库 session、外部服务 |
| Model | 使用测试数据库 | 真实数据库连接（测试库） |

## 详细文档

更详细的测试说明见 [README.md](README.md)。
