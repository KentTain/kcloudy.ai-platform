# CLAUDE.md

本文件为 Claude Code 在测试目录中工作时提供指导。

## 测试目录结构

```
tests/
├── fixtures/
│   ├── data/               # 测试数据
│   ├── helpers             # 测试辅助函数
│   └── README.md           # 测试数据说明文档
│
├── unit/                   # 单元测试
│   ├── api/                # FastAPI API 测试
│   ├── db/                 # SQLAlchemy 数据库测试
│   ├── cache/              # Redis 缓存测试
│   ├── model/              # Pydantic 模型测试
│   ├── config/             # 配置管理测试
│   ├── serialization/      # orjson 序列化测试
│   └── utils/              # 工具函数测试
│
├── studies/                # 代码预研示例（非正式测试）
│   └── examples/           # 技术探索示例
│
├── conftest.py             # pytest 全局配置
└── README.md               # 测试说明文档
```

## 运行测试

### 后端测试

```bash
# 运行所有单元测试
uv run pytest tests/unit/ -v

# 运行特定模块测试
uv run pytest tests/unit/api/ -v
uv run pytest tests/unit/db/ -v
uv run pytest tests/unit/utils/ -v

# 运行studies示例（非正式测试）
uv run pytest tests/studies/examples/ -v
```

## 测试规范

1. **单元测试** (`tests/unit/`): 使用 mock 隔离依赖
2. **代码预研** (`tests/studies/`): 技术验证代码，可不遵循严格测试规范
3. **测试标记**: 使用 `@pytest.mark.unit`, `@pytest.mark.asyncio` 等

## 常用 Fixtures

- `event_loop` - 异步事件循环
- `async_engine` - SQLAlchemy 异步引擎
- `async_session` - 数据库会话
- `cleanup_resources` - 资源清理
