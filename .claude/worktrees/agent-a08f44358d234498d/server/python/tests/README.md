# 测试说明

## 测试目录结构

```text
tests/
├── demo/                      # Demo 模块测试
│   ├── fixtures/              # 测试夹具和数据
│   ├── unit/                  # 单元测试
│   ├── examples/              # 示例代码测试
│   └── studies/               # 代码预研
│
├── framework/                 # Framework 模块测试
│   ├── fixtures/              # 测试夹具
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
│
└── conftest.py                # pytest 全局配置
```

## 测试类型

| 类型 | 说明 |
|------|------|
| 单元测试 | 使用 mock 隔离外部依赖，验证函数、类、Service 逻辑 |
| 集成测试 | 依赖真实 Redis、PostgreSQL、MinIO，必须可跳过、可清理 |
| 示例测试 | 验证 AI 示例代码可导入运行 |
| 代码预研 | 技术探索验证，不作为正式功能测试依据 |

## 运行测试

```bash
# 全部测试
uv run pytest

# 指定模块
uv run pytest tests/demo/ -v
uv run pytest tests/framework/ -v

# 指定类型
uv run pytest tests/demo/unit/ -v
uv run pytest tests/framework/integration/ -v

# 按标记运行
uv run pytest -m unit
uv run pytest -m integration

# 跳过慢测试
uv run pytest -m "not slow"
```

## 测试标记

| 标记 | 说明 |
|------|------|
| @pytest.mark.unit | 单元测试 |
| @pytest.mark.integration | 集成测试 |
| @pytest.mark.slow | 慢测试 |
| @pytest.mark.asyncio | 异步测试 |

## 开发指南

详细开发指南见上级目录的 [CLAUDE.md](../CLAUDE.md)。
