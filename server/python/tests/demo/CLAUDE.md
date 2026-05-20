# CLAUDE.md

本文件为 Claude Code 在 Demo 模块测试目录中工作时提供指导。

## 测试目录结构

```text
tests/demo/
├── fixtures/                  # 测试夹具和数据
│   ├── data/                  # 测试数据文件
│   ├── files/                 # 测试文件资源
│   └── helpers.py             # 测试辅助函数
├── unit/                      # 单元测试
│   ├── cache/                 # Redis 缓存测试
│   ├── config/                # 配置管理测试
│   ├── model/                 # Pydantic 模型测试
│   ├── serialization/         # 序列化测试
│   ├── services/              # 服务层测试
│   └── utils/                 # 工具函数测试
├── examples/                  # 示例代码测试
├── studies/                   # 代码预研（非正式测试）
│   └── examples/              # 技术探索示例
└── test_demo_imports.py       # 模块导入测试
```

## 运行测试

```bash
# 运行 Demo 模块所有测试
uv run pytest tests/demo/ -v

# 运行单元测试
uv run pytest tests/demo/unit/ -v

# 运行特定模块测试
uv run pytest tests/demo/unit/cache/ -v
uv run pytest tests/demo/unit/services/ -v

# 运行示例测试
uv run pytest tests/demo/examples/ -v

# 运行预研测试
uv run pytest tests/demo/studies/ -v
```

## 测试分类

### fixtures/ - 测试夹具

提供可重用的测试数据和辅助函数：

| 目录/文件 | 说明 |
|-----------|------|
| data/ | JSON、CSV 等测试数据文件 |
| files/ | 测试用文件资源 |
| helpers.py | 测试辅助函数 |

### unit/ - 单元测试

使用 mock 隔离依赖的单元测试：

| 目录 | 说明 |
|------|------|
| cache/ | Redis 缓存操作测试 |
| config/ | 配置加载和管理测试 |
| model/ | Pydantic 模型验证测试 |
| serialization/ | orjson 序列化测试 |
| services/ | 业务服务层测试 |
| utils/ | 工具函数测试 |

### examples/ - 示例测试

LangChain、MCP 等示例功能验证测试。

### studies/ - 代码预研

技术验证代码，非正式测试，可不遵循严格测试规范。

## 测试标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.asyncio` | 异步测试 |
| `@pytest.mark.slow` | 慢测试 |

## 使用 Fixtures

```python
# 在测试文件中导入夹具
import pytest
from tests.demo.fixtures.helpers import setup_test_data

@pytest.fixture
def test_data():
    return setup_test_data()
```

## 最佳实践

1. 保持夹具简单，专注于一个特定功能
2. 使用参数化夹具处理多种测试情景
3. 确保夹具适当清理创建的资源
4. 单元测试使用 mock 隔离外部依赖
