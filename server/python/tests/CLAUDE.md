# CLAUDE.md

本文件为 Claude Code 在测试目录中工作时提供指导。

## 测试目录结构

```
tests/
├── demo/                   # Demo 模块测试
│   ├── fixtures/
│   │   ├── data/           # 测试数据
│   │   └── helpers.py      # 测试辅助函数
│   │
│   ├── unit/               # 单元测试
│   │   ├── api/            # FastAPI API 测试
│   │   ├── db/             # SQLAlchemy 数据库测试
│   │   ├── cache/          # Redis 缓存测试
│   │   ├── model/          # Pydantic 模型测试
│   │   ├── config/         # 配置管理测试
│   │   ├── serialization/  # orjson 序列化测试
│   │   └── utils/          # 工具函数测试
│   │
│   ├── examples/           # 示例代码测试
│   │
│   └── studies/            # 代码预研示例（非正式测试）
│       └── examples/       # 技术探索示例
│
├── conftest.py             # pytest 全局配置
└── README.md               # 测试说明文档
```

## 运行测试

### 后端测试

```bash
# 运行所有测试
uv run pytest

# 运行 demo 模块测试
uv run pytest tests/demo/ -v

# 运行单元测试
uv run pytest tests/demo/unit/ -v

# 运行特定模块测试
uv run pytest tests/demo/unit/cache/ -v
uv run pytest tests/demo/unit/utils/ -v

# 运行 studies 示例（非正式测试）
uv run pytest tests/demo/studies/examples/ -v
```

## 测试规范

1. **单元测试** (`tests/demo/unit/`): 使用 mock 隔离依赖
2. **示例测试** (`tests/demo/examples/`): LangChain 等示例功能验证
3. **代码预研** (`tests/demo/studies/`): 技术验证代码，可不遵循严格测试规范
4. **测试标记**: 使用 `@pytest.mark.unit`, `@pytest.mark.asyncio` 等

## 常用 Fixtures

- `event_loop` - 异步事件循环
- `async_engine` - SQLAlchemy 异步引擎
- `async_session` - 数据库会话
- `cleanup_resources` - 资源清理
