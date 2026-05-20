# CLAUDE.md

本文件为 Claude Code 在 Python 后端测试目录中工作时提供指导。

## 测试目录结构

```text
tests/
├── demo/                      # Demo 模块测试
│   ├── fixtures/              # 测试夹具和数据
│   ├── unit/                  # 单元测试
│   ├── examples/              # 示例代码测试
│   └── studies/               # 代码预研（非正式测试）
├── framework/                 # Framework 模块测试
│   ├── fixtures/              # 测试夹具和数据
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
├── conftest.py                # pytest 全局配置
└── README.md                  # 测试说明文档
```

## 运行测试

```bash
# 运行所有测试
uv run pytest

# 详细输出
uv run pytest -v

# 运行特定模块测试
uv run pytest tests/demo/unit/ -v
uv run pytest tests/framework/unit/ -v
uv run pytest tests/framework/integration/ -v

# 跳过慢测试
uv run pytest -m "not slow"

# 遇到第一个失败即停止
uv run pytest -x
```

## 测试规范

### Demo 模块测试

| 目录 | 说明 |
|------|------|
| fixtures/ | 测试数据和辅助函数 |
| unit/ | 单元测试（使用 mock 隔离依赖） |
| examples/ | LangChain 等示例功能验证 |
| studies/ | 技术验证代码，非正式测试 |

### Framework 模块测试

| 目录 | 说明 |
|------|------|
| fixtures/ | 测试夹具、辅助函数和配置 |
| unit/ | 单元测试（使用 mock 隔离依赖） |
| integration/ | 集成测试（需要真实服务） |

## 测试标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.slow` | 慢测试 |
| `@pytest.mark.db` | 数据库测试 |
| `@pytest.mark.api` | API 测试 |
| `@pytest.mark.asyncio` | 异步测试 |

## 常用 Fixtures

| Fixture | 说明 |
|---------|------|
| `event_loop` | 异步事件循环 |
| `async_engine` | SQLAlchemy 异步引擎 |
| `async_session` | 数据库会话 |
| `cleanup_resources` | 资源清理 |

## 详细文档

- **Demo 测试**：[demo/CLAUDE.md](demo/CLAUDE.md)
- **Framework 测试**：[framework/CLAUDE.md](framework/CLAUDE.md)
