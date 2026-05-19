# 测试说明

> 详细测试规范见 [CLAUDE.md](CLAUDE.md)

## 测试目录结构

本项目的测试目录采用分层结构组织，按模块划分：

```
tests/
├── demo/                   # Demo 模块测试
│   ├── unit/               # 单元测试
│   │   ├── apis/           # API 层单元测试
│   │   ├── services/       # 业务服务层单元测试
│   │   ├── models/         # 数据模型单元测试
│   │   ├── utils/          # 工具函数单元测试
│   │   ├── cache/          # 缓存单元测试
│   │   └── schemas/        # 数据验证模式单元测试
│   │
│   ├── examples/           # 示例代码测试
│   │   ├── agent_core/     # Agent 核心测试
│   │   ├── code_plugins/   # 代码插件测试
│   │   ├── custom_tools/   # 自定义工具测试
│   │   ├── http_plugins/   # HTTP 插件测试
│   │   ├── langgraph_workflows/  # LangGraph 工作流测试
│   │   ├── mcp_tools/      # MCP 工具测试
│   │   ├── prompt_engineering/  # Prompt 工程测试
│   │   └── rag_knowledge_base/  # RAG 知识库测试
│   │
│   ├── studies/            # 代码预研 (非测试)
│   │   ├── examples/       # 技术探索示例
│   │   └── langchain_study/  # LangChain 学习
│   │   └── langgraph_study/  # LangGraph 学习
│   │
│   └── fixtures/           # 测试夹具和数据
│       ├── data/           # 测试数据文件
│       └── helpers.py      # 测试辅助函数
│
├── conftest.py             # 全局测试配置和夹具
└── __init__.py             # 包初始化
```

## 测试类型说明

1. **单元测试（Unit Tests）**：测试独立的代码单元，如函数、方法或类
2. **示例测试（Example Tests）**：验证 LangChain、LangGraph 等示例功能
3. **代码预研（Studies）**：用于技术探索和验证的代码示例，非正式测试

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

# 运行 demo 模块测试
uv run pytest tests/demo/

# 运行特定类型的测试
uv run pytest tests/demo/unit/
uv run pytest tests/demo/examples/

# 使用标记运行测试
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m api
uv run pytest -m db

# 跳过慢速测试
uv run pytest -k "not slow"
```

## 测试环境

测试环境配置在 `conftest.py` 中，主要包括：

1. 设置环境变量 `PYTHON_SERVICE_ENV=local`
2. 提供共享夹具
3. 设置异步事件循环

## 代码预研区域

`studies` 目录用于存放代码预研和技术探索，这些不是正式测试但对技术验证很有价值。预研代码不必遵循严格的测试规范。
