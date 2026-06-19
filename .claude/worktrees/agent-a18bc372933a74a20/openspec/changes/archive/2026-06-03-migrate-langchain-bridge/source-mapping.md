# LangChain 桥接层实现参考

本文档记录 `migrate-langchain-bridge` 变更的实现参考，包括参考文档和相关资源。

## 参考文档

### 设计文档

| 文档 | 路径 | 说明 |
|------|------|------|
| LangChain 替换 Agno 方案 | `docs/designs/AI框架由LangChain替换Agno.md` | 完整的迁移方案和代码示例 |

### LangChain 官方文档

| 主题 | 链接 |
|------|------|
| 自定义 ChatModel | https://python.langchain.com/docs/how_to/custom_chat_model/ |
| BaseChatModel API | https://api.python.langchain.com/en/latest/language_models/langchain_core.language_models.chat_models.BaseChatModel.html |
| AgentExecutor | https://python.langchain.com/docs/modules/agents/ |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| 消息类型 | https://python.langchain.com/docs/modules/memory/chat_messages/ |

## 项目现有资源

### LangGraph 示例

项目已有 LangGraph 使用示例，可作为参考：

| 文件 | 路径 | 说明 |
|------|------|------|
| 记忆与检查点示例 | `src/demo/examples/langgraph_workflows/memory_checkpoint_demo.py` | LangGraph 状态管理示例 |
| 条件路由示例 | `src/demo/examples/langgraph_workflows/conditional_routing_demo.py` | 条件分支示例 |
| 并行执行示例 | `src/demo/examples/langgraph_workflows/parallel_execution_demo.py` | 并行节点示例 |
| 错误处理示例 | `src/demo/examples/langgraph_workflows/error_handler_demo.py` | 错误处理示例 |
| MCP LangGraph 示例 | `src/demo/examples/mcp_tools/mcp_langgraph_demo.py` | MCP 工具集成示例 |

### 已有组件

| 组件 | 路径 | 说明 |
|------|------|------|
| PromptMessage | `src/ai_plugin/sdk/entities/model/message.py` | 平台消息实体 |
| LLMResult | `src/ai_plugin/sdk/entities/model/llm.py` | 平台 LLM 结果实体 |
| LLMService | `src/ai/components/model/services/llm_service.py` | LLM 服务（待迁移） |

## 核心实现参考

### AlonChatModel 类结构

```python
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk

class AlonChatModel(BaseChatModel):
    """LangChain 自定义 ChatModel，桥接到平台 LLMService"""

    model: str                    # 模型名称
    provider: str                 # Provider ID
    tenant_id: str                # 租户 ID
    user_id: str | None = None    # 用户 ID
    model_parameters: dict = {}   # 模型参数

    @property
    def _llm_type(self) -> str:
        return "alon-chat-model"

    @property
    def _identifying_params(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "tenant_id": self.tenant_id,
        }

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError("请使用异步方法 ainvoke")

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        """异步非流式调用"""
        # 1. 转换消息类型
        # 2. 调用 LLMService.invoke()
        # 3. 转换结果为 ChatResult
        ...

    async def _astream(self, messages, stop=None, run_manager=None, **kwargs):
        """异步流式调用"""
        # 1. 转换消息类型
        # 2. 调用 LLMService.stream()
        # 3. 逐块转换为 ChatGenerationChunk
        ...
```

### MessageAdapter 类结构

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from ai_plugin.sdk.entities.model.message import (
    UserPromptMessage,
    AssistantPromptMessage,
    SystemPromptMessage,
    PromptMessage,
)

class MessageAdapter:
    """消息类型双向转换器"""

    @staticmethod
    def to_platform_message(message: BaseMessage) -> PromptMessage:
        """LangChain 消息 → 平台消息"""
        match message:
            case HumanMessage():
                return UserPromptMessage(content=message.content)
            case AIMessage():
                return AssistantPromptMessage(content=message.content)
            case SystemMessage():
                return SystemPromptMessage(content=message.content)
            case _:
                raise UnsupportedMessageTypeError(f"不支持的消息类型: {type(message)}")

    @staticmethod
    def to_langchain_message(message: PromptMessage) -> BaseMessage:
        """平台消息 → LangChain 消息"""
        match message:
            case UserPromptMessage():
                return HumanMessage(content=message.content)
            case AssistantPromptMessage():
                return AIMessage(content=message.content)
            case SystemPromptMessage():
                return SystemMessage(content=message.content)
            case _:
                raise UnsupportedMessageTypeError(f"不支持的消息类型: {type(message)}")
```

### AgentFactory 类结构

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

class AgentFactory:
    """Agent 创建工厂"""

    def __init__(self, model: AlonChatModel):
        self.model = model

    def create_executor(
        self,
        tools: list,
        memory: ConversationBufferMemory | None = None,
        prompt: ChatPromptTemplate | None = None,
        verbose: bool = False,
        handle_parsing_errors: bool = True,
    ) -> AgentExecutor:
        """创建 AgentExecutor"""
        if prompt is None:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个有帮助的 AI 助手。"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

        agent = create_tool_calling_agent(self.model, tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=verbose,
            handle_parsing_errors=handle_parsing_errors,
        )
```

## 版本要求

```toml
[project.dependencies]
langchain = "1.3.0"
langchain-core = ">=0.3.0"
langchain-community = ">=0.3.0"
langgraph = "1.2.0"
```

## 文件数量统计

| 类别 | 文件数 |
|------|--------|
| 必须实现 | 3 |
| 测试文件 | 3-5 |
| 文档 | 1 |
| **总计** | **7-9** |
