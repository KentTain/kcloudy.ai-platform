# LangChain & LangGraph 演示示例

本目录包含 AI 智能体应用实战（Day 3 & Day 4 讲义）的演示代码，涵盖提示词工程、自定义工具开发、LangGraph 工作流编排、MCP 工具集成、RAG 知识库构建以及智能体开发实战。

## 目录结构

```
src/demo/examples/
├── __init__.py              # 模块入口
├── prompt_engineering/      # 提示词工程示例
│   ├── __init__.py
│   ├── prompt_template_demo.py    # PromptTemplate 基础
│   ├── few_shot_demo.py           # FewShotPromptTemplate
│   └── output_parser_demo.py      # 输出解析器
├── custom_tools/            # 自定义工具示例
│   ├── __init__.py
│   ├── basic_tool_demo.py         # @tool 装饰器
│   ├── structured_tool_demo.py    # StructuredTool
│   └── tool_chain_demo.py         # 工具链编排
├── langgraph_workflows/     # LangGraph 工作流示例
│   ├── __init__.py
│   ├── state_graph_demo.py        # StateGraph 基础
│   ├── conditional_routing_demo.py # 条件路由
│   └── memory_checkpoint_demo.py  # 记忆与检查点
├── mcp_tools/               # MCP 工具集成示例
│   ├── __init__.py
│   ├── mcp_client_demo.py         # MCP 客户端配置
│   ├── mcp_tool_invoke_demo.py    # MCP 工具调用
│   └── mcp_langgraph_demo.py      # MCP + LangGraph
├── rag_knowledge_base/       # RAG 知识库示例（Day 4）
│   ├── __init__.py
│   ├── pdf_parser_demo.py         # PDF 解析
│   ├── text_splitter_demo.py      # 文档分段
│   ├── embedding_demo.py          # Embedding 生成
│   ├── vector_store_demo.py       # 向量存储与检索
│   └── rag_pipeline_demo.py       # 完整 RAG 流程
├── agent_core/               # 智能体核心逻辑（Day 4）
│   ├── __init__.py
│   ├── persona_demo.py            # 人设配置
│   ├── knowledge_base_demo.py     # 知识库关联
│   ├── workflow_demo.py           # LangGraph 工作流
│   └── agent_demo.py              # 完整智能体
├── http_plugins/             # HTTP 插件示例（Day 4）
│   ├── __init__.py
│   ├── weather_plugin_demo.py     # 天气查询插件
│   ├── error_handling_demo.py     # 错误处理与重试
│   └── mock_data_demo.py          # Mock 数据
└── code_plugins/             # 代码插件示例（Day 4）
    ├── __init__.py
    ├── code_qa_plugin_demo.py     # 代码问答插件
    ├── keyword_match_demo.py      # 关键词匹配
    └── plugin_integration_demo.py # LangGraph 集成
```

## 安装依赖

```bash
# 安装 LangChain 相关依赖
uv sync --group langchain
```

## 快速开始

### 1. 提示词工程

```python
from demo.examples.prompt_engineering import (
    create_prompt_template,
    create_few_shot_prompt,
)

# 创建提示词模板
template = create_prompt_template(
    template="你好，{name}！你是{role}。",
    input_variables=["name", "role"]
)
result = template.format(name="小明", role="开发者")
print(result)  # 你好，小明！你是开发者。
```

### 2. 自定义工具

```python
from demo.examples.custom_tools import CalculatorTool

# 使用计算器工具
result = CalculatorTool.add.invoke({"a": 2, "b": 3})
print(result)  # 5

# 获取所有工具
tools = CalculatorTool.get_tools()
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
```

### 3. LangGraph 工作流

```python
from demo.examples.langgraph_workflows import (
    create_simple_workflow,
    WorkflowState,
)

# 创建并执行工作流
app = create_simple_workflow()
state = WorkflowState(query="分析销售数据")
result = app.invoke(state)
print(result["result"])
```

### 4. MCP 工具集成

```python
from demo.examples.mcp_tools import MCPToolInvoker

# 创建工具调用器
invoker = MCPToolInvoker()

# 调用 MCP 工具
result = invoker.invoke("mcp_weather", city="北京")
print(result)
```

### 5. RAG 知识库（Day 4）

```python
from demo.examples.rag_knowledge_base import SimpleRAGPipeline

# 创建 RAG 管道
rag = SimpleRAGPipeline()

# 添加文档
rag.add_text("""
第1章 Python 简介
Python 是一种解释型编程语言。

第2章 函数定义
使用 def 关键字定义函数。
""")

# 查询
result = rag.query("Python 如何定义函数？")
print(result["context"])
```

### 6. 智能体核心（Day 4）

```python
from demo.examples.agent_core import SimpleAgent, PersonaConfig

# 配置人设
persona = PersonaConfig(template_name="python_expert")

# 创建智能体
agent = SimpleAgent(persona_config=persona)
agent.add_knowledge(["Python 使用 def 定义函数"])

# 对话
response = agent.chat("Python 函数怎么写？")
print(response["response"])
```

### 7. HTTP 插件（Day 4）

```python
from demo.examples.http_plugins import WeatherPlugin

# 创建天气插件
plugin = WeatherPlugin(use_mock=True)

# 查询天气
result = plugin.get_weather("北京")
print(f"温度: {result['temperature']}, 天气: {result['weather']}")
```

### 8. 代码插件（Day 4）

```python
from demo.examples.code_plugins import PythonCodeQA

# 创建代码问答插件
plugin = PythonCodeQA()

# 查询代码示例
code = plugin.query("Python 函数示例")
print(code)
```

## 模块说明

### prompt_engineering - 提示词工程

| 文件 | 说明 |
|------|------|
| `prompt_template_demo.py` | PromptTemplate 基础用法，变量替换、部分绑定 |
| `few_shot_demo.py` | FewShotPromptTemplate 少样本学习 |
| `output_parser_demo.py` | PydanticOutputParser、JsonOutputParser |

### custom_tools - 自定义工具

| 文件 | 说明 |
|------|------|
| `basic_tool_demo.py` | @tool 装饰器创建简单工具 |
| `structured_tool_demo.py` | StructuredTool 复杂工具定义 |
| `tool_chain_demo.py` | 工具链顺序执行、条件分支 |

### langgraph_workflows - LangGraph 工作流

| 文件 | 说明 |
|------|------|
| `state_graph_demo.py` | StateGraph 状态图基础 |
| `conditional_routing_demo.py` | 条件边、动态路由 |
| `memory_checkpoint_demo.py` | 检查点、会话持久化 |

### mcp_tools - MCP 工具集成

| 文件 | 说明 |
|------|------|
| `mcp_client_demo.py` | MCP 客户端配置与连接 |
| `mcp_tool_invoke_demo.py` | MCP 工具调用封装 |
| `mcp_langgraph_demo.py` | MCP 工具与 LangGraph 集成 |

### rag_knowledge_base - RAG 知识库示例（Day 4）

| 文件 | 说明 |
|------|------|
| `pdf_parser_demo.py` | PDF 文档解析，提取纯文本，去除页眉页脚 |
| `text_splitter_demo.py` | 文档分段，按章节/句子/长度分割 |
| `embedding_demo.py` | Embedding 向量生成，Mock 实现 |
| `vector_store_demo.py` | 内存向量存储与相似度检索 |
| `rag_pipeline_demo.py` | 完整 RAG 流程：解析→分段→向量化→检索 |

### agent_core - 智能体核心逻辑（Day 4）

| 文件 | 说明 |
|------|------|
| `persona_demo.py` | 智能体人设配置：角色、语气、系统提示词 |
| `knowledge_base_demo.py` | 知识库关联与检索增强 |
| `workflow_demo.py` | LangGraph StateGraph 工作流编排 |
| `agent_demo.py` | 完整智能体：整合四大支柱 |

### http_plugins - HTTP 插件示例（Day 4）

| 文件 | 说明 |
|------|------|
| `weather_plugin_demo.py` | 天气查询 HTTP 插件，@tool 装饰器 |
| `error_handling_demo.py` | 错误处理、超时、自动重试机制 |
| `mock_data_demo.py` | Mock 数据提供，场景切换 |

### code_plugins - 代码插件示例（Day 4）

| 文件 | 说明 |
|------|------|
| `code_qa_plugin_demo.py` | 代码问答插件，预设 Python 示例 |
| `keyword_match_demo.py` | 关键词匹配，优先级排序 |
| `plugin_integration_demo.py` | 插件注册表与 LangGraph 工具节点 |

## 运行示例

```bash
# 运行提示词工程示例
uv run python -m demo.examples.prompt_engineering.prompt_template_demo

# 运行自定义工具示例
uv run python -m demo.examples.custom_tools.basic_tool_demo

# 运行 LangGraph 工作流示例
uv run python -m demo.examples.langgraph_workflows.state_graph_demo

# 运行 MCP 工具示例
uv run python -m demo.examples.mcp_tools.mcp_client_demo

# 运行 RAG 知识库示例（Day 4）
uv run python -m demo.examples.rag_knowledge_base.rag_pipeline_demo

# 运行智能体核心示例（Day 4）
uv run python -m demo.examples.agent_core.agent_demo

# 运行 HTTP 插件示例（Day 4）
uv run python -m demo.examples.http_plugins.weather_plugin_demo

# 运行代码插件示例（Day 4）
uv run python -m demo.examples.code_plugins.code_qa_plugin_demo
```

## 运行测试

```bash
# 运行所有示例测试
uv run pytest tests/examples/ -v

# 运行特定模块测试
uv run pytest tests/examples/test_prompt_engineering.py -v
uv run pytest tests/examples/test_custom_tools.py -v
uv run pytest tests/examples/test_langgraph_workflows.py -v
uv run pytest tests/examples/test_mcp_tools.py -v

# 运行 Day 4 示例测试
uv run pytest tests/examples/test_rag_knowledge_base.py -v
uv run pytest tests/examples/test_agent_core.py -v
uv run pytest tests/examples/test_http_plugins.py -v
uv run pytest tests/examples/test_code_plugins.py -v
```

## 注意事项

1. **模拟实现**：MCP 工具示例使用模拟实现，实际使用需要配置真实的 MCP 服务器。

2. **API Key**：部分示例（如 FewShotPromptTemplate 的语义选择器）需要 OpenAI API Key。

3. **离线测试**：单元测试使用 mock 模拟 LLM 调用，可以离线运行。

## 扩展阅读

- [LangChain 官方文档](https://python.langchain.com/)
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
