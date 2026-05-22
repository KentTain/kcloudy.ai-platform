# Demo 模块测试指南

本文件为 Claude Code 在 `tests/demo/` 中编写和维护 demo 模块测试时提供指导。

## 测试范围

Demo 测试覆盖业务演示模块、AI 示例代码、工具函数、Pydantic 模型、序列化、缓存示例和技术预研代码。`studies/` 属于预研验证，不按正式测试质量要求约束。

## 目录职责

| 目录 / 文件 | 职责 |
| --- | --- |
| `fixtures/` | 可复用测试数据、文件资源和辅助函数 |
| `fixtures/data/` | JSON、Swagger、OAuth、AI 工具等测试数据 |
| `unit/` | 单元测试，使用 mock 隔离外部依赖 |
| `examples/` | LangChain、LangGraph、MCP、插件、RAG 等示例测试 |
| `studies/` | 技术预研验证代码，非正式测试 |
| `test_demo_imports.py` | Demo 模块导入检查 |

## 运行命令

```bash
# Demo 模块全部测试
uv run pytest tests/demo/ -v

# 单元测试
uv run pytest tests/demo/unit/ -v

# 示例测试
uv run pytest tests/demo/examples/ -v

# 预研测试
uv run pytest tests/demo/studies/ -v
```

按主题运行：

```bash
uv run pytest tests/demo/unit/cache/ -v
uv run pytest tests/demo/unit/services/ -v
uv run pytest tests/demo/unit/model/ -v
uv run pytest tests/demo/unit/serialization/ -v
```

## 测试标记

| 标记 | 说明 |
| --- | --- |
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.asyncio` | 异步测试 |
| `@pytest.mark.slow` | 慢测试 |

## 单元测试约定

- `unit/cache/`：验证 Redis 示例封装、序列化和过期行为，默认使用 mock 或可控测试替身。
- `unit/model/`：验证 Pydantic 字段校验、约束和序列化。
- `unit/services/`：验证 Service 业务逻辑，隔离数据库、缓存、外部 API。
- `unit/serialization/`：验证 orjson 等序列化行为。
- `unit/utils/`：验证工具函数的边界输入与异常输入。

## 示例测试约定

`examples/` 用于验证 AI 示例代码可以导入、运行关键路径并保持演示语义稳定。涉及外部模型、网络或第三方服务时，应使用 mock、fixture 数据或跳过条件，避免测试依赖真实远端服务。

重点覆盖：

- Agent Core 示例。
- Code / HTTP 插件示例。
- Custom Tools 示例。
- LangGraph 工作流和异常处理。
- MCP 工具示例。
- Prompt Engineering 示例。
- RAG Knowledge Base 示例。

## fixtures 使用规则

- 测试数据放在 `fixtures/data/`，不要在测试函数中内联大段 JSON。
- 文件资源放在 `fixtures/files/`（如存在），测试后不要修改原始 fixture。
- `fixtures/helpers.py` 只放跨多个测试复用的轻量辅助函数。
- 新增 fixture 时优先保持纯函数和显式输入，避免隐藏全局状态。

## studies 规则

`studies/` 是技术探索区，可以包含不稳定或实验性的测试代码。修改正式功能时，不应只依赖 `studies/` 证明行为正确；需要在 `unit/` 或 `examples/` 中补充正式测试。
