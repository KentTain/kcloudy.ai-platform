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

## 编写测试规则

- 测试路径应反映被测模块和能力，例如 `tests/framework/unit/cache/` 对应 `src/framework/cache/`。
- 单元测试不要访问真实网络、数据库、Redis 或对象存储。
- 集成测试必须检测依赖服务可用性；不可用时跳过相关测试。
- 测试数据应放在 `fixtures/`，避免在测试函数中内联大段 JSON 或二进制内容。
- 异步代码使用 `@pytest.mark.asyncio`。
- 修复 bug 时先补充能复现问题的测试，再修改实现。
- 新增模块时同步新增 `tests/{module}/`，必要时补充模块级 `CLAUDE.md`。

## 详细文档

更详细的测试说明见 [README.md](README.md)。
