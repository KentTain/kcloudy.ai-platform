# Python 后端测试指南

本文件为 Claude Code 在 `server/python/tests/` 测试目录中工作时提供指导。

## 目录定位

`tests/` 按源码模块组织测试。模块测试目录与 `src/{module}/` 对齐：

| 测试目录 | 对应源码 | 详细文档 |
| --- | --- | --- |
| `demo/` | `src/demo/` | [demo/CLAUDE.md](demo/CLAUDE.md) |
| `framework/` | `src/framework/` | [framework/CLAUDE.md](framework/CLAUDE.md) |

IAM 相关测试可按当前覆盖点放在对应集成测试或后续新增 `tests/iam/`，但测试命名与源码模块边界应保持一致。

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
uv run pytest tests/framework/unit/ -v
uv run pytest tests/framework/integration/ -v
```

## 测试类型

| 类型 | 目录 | 约定 |
| --- | --- | --- |
| 单元测试 | `tests/{module}/unit/` | 使用 mock 或测试替身隔离外部依赖，验证函数、类和 Service 逻辑 |
| 集成测试 | `tests/{module}/integration/` | 使用真实 Redis、PostgreSQL、MinIO 或跨组件协作，必须可跳过、可清理 |
| 示例测试 | `tests/demo/examples/` | 验证 AI 示例代码可导入、可运行关键路径 |
| 预研测试 | `tests/demo/studies/` | 技术探索，不作为正式功能验证的唯一依据 |
| 夹具 | `tests/{module}/fixtures/` | 测试数据、文件资源、辅助函数 |

## pytest 标记

| 标记 | 说明 |
| --- | --- |
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.slow` | 慢测试 |
| `@pytest.mark.db` | 数据库测试 |
| `@pytest.mark.api` | API 测试 |
| `@pytest.mark.asyncio` | 异步测试 |

## 通用 fixtures

| Fixture | 说明 |
| --- | --- |
| `event_loop` | 异步事件循环 |
| `async_engine` | SQLAlchemy 异步引擎 |
| `async_session` | 数据库会话 |
| `cleanup_resources` | 资源清理 |

模块专属 fixtures 见对应模块测试文档。

## 编写测试规则

- 测试路径应反映被测模块和能力，例如 `tests/framework/unit/cache/` 对应 `src/framework/cache/`。
- 单元测试不要访问真实网络、数据库、Redis 或对象存储。
- 集成测试必须检测依赖服务可用性；不可用时跳过相关测试。
- 测试数据应放在 `fixtures/`，避免在测试函数中内联大段 JSON 或二进制内容。
- 异步代码使用 `@pytest.mark.asyncio`。
- 修复 bug 时先补充能复现问题的测试，再修改实现。
- 新增模块时同步新增 `tests/{module}/`，必要时补充模块级 `CLAUDE.md`。
