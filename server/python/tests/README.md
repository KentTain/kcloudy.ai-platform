# 测试说明

> 详细测试规范见 [CLAUDE.md](CLAUDE.md)

## 测试目录结构

本项目的测试目录采用分层结构组织，主要包括：

```
tests/
├── unit/               # 单元测试
│   ├── apis/           # API层单元测试
│   ├── services/       # 业务服务层单元测试
│   ├── models/         # 数据模型单元测试
│   ├── utils/          # 工具函数单元测试
│   └── schemas/        # 数据验证模式单元测试
│
├── integration/        # 集成测试
│   ├── api_flows/      # API流程集成测试
│   ├── db/             # 数据库操作集成测试
│   └── services/       # 服务间集成测试
│
├── components/         # 组件测试
│   ├── oss/            # 对象存储测试
│   ├── redis/          # Redis测试
│   └── postgresql/     # PostgreSQL测试
│
├── e2e/                # 端到端测试
│   └── api/            # API端到端测试
│
├── studies/            # 代码预研 (非测试)
│   ├── asyncio/        # 异步操作相关研究
│   ├── websocket/      # WebSocket相关研究
│   ├── zk/             # ZooKeeper相关研究
│   └── examples/       # 其他技术探索示例
│
├── fixtures/           # 测试夹具和数据
│   ├── data/           # 测试数据文件
│   └── helpers.py      # 测试辅助函数
│
├── conftest.py         # 全局测试配置和夹具
└── pytest.ini          # pytest配置文件
```

## 测试类型说明

1. **单元测试（Unit Tests）**：测试独立的代码单元，如函数、方法或类
2. **集成测试（Integration Tests）**：测试多个组件或服务之间的交互
3. **组件测试（Component Tests）**：测试特定组件（如OSS、Redis）的功能
4. **端到端测试（E2E Tests）**：测试完整的应用流程
5. **代码预研（Studies）**：用于技术探索和验证的代码示例，非正式测试

## 运行测试

### 安装依赖

确保已安装测试所需的依赖：

```bash
uv sync
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定类型的测试
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/components
uv run pytest tests/e2e

# 使用标记运行测试
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m api
uv run pytest -m db
uv run pytest -m redis

# 跳过慢速测试
uv run pytest -k "not slow"

# 生成报告
uv run pytest --html=report.html
```

## 测试环境

测试环境配置在 `conftest.py` 中，主要包括：

1. 设置环境变量
2. 提供共享夹具
3. 设置异步事件循环

## 代码预研区域

`studies` 目录用于存放代码预研和技术探索，这些不是正式测试但对技术验证很有价值。预研代码不必遵循严格的测试规范。
