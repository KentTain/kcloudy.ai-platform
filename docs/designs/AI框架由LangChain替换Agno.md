# Agno → LangChain 框架替换指南

## 一、替换范围总览

将 /portal/v1/chat-messages 接口从 agno 框架迁移到 LangChain，涉及以下核心组件：

| agno 组件 | LangChain 对应 | 影响范围 |
|-----------|----------------|----------|
| Alon(Model) | BaseChatModel 自定义实现 | 步骤 6 |
| Agent(RawAgent) | AgentExecutor 或 LangGraph | 步骤 6、步骤 1 |
| MemoryManager | ConversationBufferMemory / ConversationSummaryMemory | 步骤 1 |
| CompressionManager | 无直接对应，需自定义或省略 | 步骤 1 |
| SessionSummaryManager | ConversationSummaryMemory 或自定义 | 步骤 1 |
| RunEvent / RunOutputEvent | AsyncCallbackHandler | 步骤 1 |
| Message | BaseMessage 系列 | 步骤 1、步骤 6 |
| get_db() | PostgresChatMessageHistory | 步骤 1、步骤 6 |
| BaiduSearchTools | 自定义 Tool 或 BingSearchRun | 步骤 1 |

---

## 二、依赖变更

### 2.1 移除 agno，添加 LangChain

```bash

# 移除

uv remove agno

# 添加 LangChain 核心包

uv add langchain langchain-core langchain-community

# 添加消息历史持久化

uv add langchain-postgres

# 可选：如果使用 LangGraph（推荐用于复杂 Agent）

uv add langgraph
```

### 2.2 版本建议

``` oml
langchain = [
  # LangChain 核心
  "langchain[community]==1.3.0",
  # LangGraph 工作流
  "langgraph==1.2.0",
  # OpenAI 集成
  "langchain-openai>=0.3.0",
  # MCP 集成
  "langchain-mcp-adapters>=0.1.0",
  # RAG 知识库示例
  "pypdf>=5.0.0",
]
```

---

## 三、详细替换方案

---

### 3.1 模型类替换（步骤 6 核心改动）

#### 原实现（agno）

```python

# extended/agno/models/alon/alon.py

from agno.models.base import Model

@dataclass
class Alon(Model):
    \"\"\"继承 agno.Model，实现 ainvoke / ainvoke_stream\"\"\"

    async def ainvoke(self, messages, assistant_message, ...):
        llm_service = self._get_platform_models().llm
        async_stream = llm_service.stream(
            model=self.id,
            prompt_messages=self._format_messages(messages),
            provider=self.provider,
            ...
        )
        # 收集流式响应并返回
```

#### LangChain 替换方案

```python

# extended/langchain/models/alon_chat.py

from typing import Any, AsyncIterator, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from <newpkg>.components.model.services.llm_service import LLMService
from <newpkg>_plugin.sdk.entities.model.message import (
    PromptMessage,
    UserPromptMessage,
    AssistantPromptMessage,
    SystemPromptMessage,
)

class AlonChatModel(BaseChatModel):
    \"\"\"
    LangChain 自定义 ChatModel，桥接到平台 LLMService

    用法：
        model = AlonChatModel(
            model=\"gpt-4\",
            provider=\"plugin_id/openai\",
            tenant_id=\"xxx\",
            temperature=0.7,
        )
        response = await model.ainvoke([HumanMessage(content=\"你好\")])
    \"\"\"
    
    model: str
    provider: str
    tenant_id: str
    user_id: Optional[str] = None
    model_parameters: dict = {}
    
    @property
    def _llm_type(self) -> str:
        return \"alon-chat-model\"
    
    @property
    def _identifying_params(self) -> dict:
        return {
            \"model\": self.model,
            \"provider\": self.provider,
            \"tenant_id\": self.tenant_id,
        }
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[PromptMessage]:
        \"\"\"将 LangChain BaseMessage 转换为平台 PromptMessage\"\"\"
        result = []
        for msg in messages:
            if msg.type == \"human\":
                result.append(UserPromptMessage(content=msg.content))
            elif msg.type == \"ai\":
                result.append(AssistantPromptMessage(content=msg.content))
            elif msg.type == \"system\":
                result.append(SystemPromptMessage(content=msg.content))
            # 可扩展处理 tool、function 等类型
        return result
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        \"\"\"同步调用（LangChain 要求实现，这里抛出异常）\"\"\"
        raise NotImplementedError(\"请使用异步方法 ainvoke\")
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        \"\"\"异步非流式调用\"\"\"
        llm_service = LLMService(self.tenant_id)
        
        prompt_messages = self._convert_messages(messages)
        
        result = await llm_service.invoke(
            prompt_messages=prompt_messages,
            model=self.model,
            provider=self.provider,
            model_parameters={**self.model_parameters, \"stop\": stop},
            user=self.user_id,
        )
        
        # 将 LLMResult 转换为 ChatResult
        ai_message = AIMessage(content=result.message.content or \"\")
        
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=ai_message,
                    generation_info={
                        \"prompt_tokens\": result.usage.prompt_tokens,
                        \"completion_tokens\": result.usage.completion_tokens,
                        \"total_tokens\": result.usage.total_tokens,
                    },
                )
            ],
            llm_output={\"model\": self.model},
        )
    
    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        \"\"\"异步流式调用\"\"\"
        llm_service = LLMService(self.tenant_id)
        
        prompt_messages = self._convert_messages(messages)
        
        async for chunk in llm_service.stream(
            prompt_messages=prompt_messages,
            model=self.model,
            provider=self.provider,
            model_parameters={**self.model_parameters, \"stop\": stop},
            user=self.user_id,
        ):
            # chunk 是 LLMResultChunk
            if chunk.message and chunk.message.content:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=chunk.message.content),
                    generation_info={
                        \"prompt_tokens\": chunk.usage.prompt_tokens if chunk.usage else 0,
                        \"completion_tokens\": chunk.usage.completion_tokens if chunk.usage else 0,
                    },
                )
```

#### 关键差异

| 对比项 | agno.Model | LangChain BaseChatModel |
|--------|-----------|------------------------|
| 消息类型 | gno.models.message.Message | langchain_core.messages.BaseMessage |
| 流式返回 | ModelResponse | ChatGenerationChunk |
| 非流式返回 | ModelResponse | ChatResult |
| 方法签名 | invoke(messages, assistant_message, ...) | _agenerate(messages, stop, ...) |
| 流式方法 | invoke_stream(messages, ...) | _astream(messages, ...) |

---

### 3.2 Agent 替换（步骤 6 + 步骤 1）

#### 原实现（agno）

```python

# 控制器中

from extended.agno.agent import Agent

agent = Agent(
    id=APP_ID,
    model=model,                      # Alon 模型
    tools=[BaiduSearchTools()],
    memory_manager=memory_manager,
    session_summary_manager=session_summary_manager,
    compression_manager=compression_manager,
    db=db,
    stream=True,
    stream_events=True,
)

response_stream = agent.arun(input=query)
async for response in response_stream:
    if response.event == RunEvent.run_content:
        yield response.content
```

#### LangChain 替换方案 A：AgentExecutor（简单场景）

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

# 1. 创建 Prompt

prompt = ChatPromptTemplate.from_messages([
    (\"system\", \"你是一个有帮助的 AI 助手。\"),
    MessagesPlaceholder(variable_name=\"chat_history\"),
    (\"human\", \"{input}\"),
    MessagesPlaceholder(variable_name=\"agent_scratchpad\"),  # 工具调用中间步骤
])

# 2. 创建 Agent

agent = create_tool_calling_agent(
    llm=model,           # AlonChatModel 实例
    tools=tools,         # LangChain Tool 列表
    prompt=prompt,
)

# 3. 创建 Memory

memory = ConversationBufferMemory(
    memory_key=\"chat_history\",
    return_messages=True,
)

# 4. 创建 AgentExecutor

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
)

# 5. 执行（非流式）

result = await agent_executor.ainvoke({\"input\": query})
print(result[\"output\"])

# 6. 执行（流式）

async for event in agent_executor.astream_events({\"input\": query}, version=\"v2\"):
    if event[\"event\"] == \"on_chat_model_stream\":
        chunk = event[\"data\"][\"chunk\"]
        yield chunk.content
```

#### LangChain 替换方案 B：LangGraph（推荐，功能更完整）

LangGraph 是 LangChain 团队推荐的 Agent 框架，支持复杂状态管理和循环。

```python
from typing import Annotated, TypedDict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.managed import IsLastStep

# 1. 定义状态

class AgentState(TypedDict):
    messages: Annotated[list, \"对话消息列表\"]
    is_last_step: IsLastStep

# 2. 创建工具节点

tool_node = ToolNode(tools)

# 3. 创建模型调用节点

async def call_model(state: AgentState):
    response = await model.ainvoke(state[\"messages\"])
    return {\"messages\": [response]}

# 4. 构建图

workflow = StateGraph(AgentState)
workflow.add_node(\"agent\", call_model)
workflow.add_node(\"tools\", tool_node)
workflow.set_entry_point(\"agent\")

# 5. 添加条件边

def should_continue(state: AgentState):
    messages = state[\"messages\"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return \"tools\"
    return \"end\"

workflow.add_conditional_edges(\"agent\", should_continue, {
    \"tools\": \"tools\",
    \"end\": \"__end__\",
})
workflow.add_edge(\"tools\", \"agent\")

# 6. 配置持久化（PostgreSQL）

checkpointer = AsyncPostgresSaver(conn_string)

# 7. 编译

app = workflow.compile(checkpointer=checkpointer)

# 8. 执行（流式）

config = {\"configurable\": {\"thread_id\": conversation_id}}
async for event in app.astream_events(
    {\"messages\": [HumanMessage(content=query)]},
    config=config,
    version=\"v2\",
):
    if event[\"event\"] == \"on_chat_model_stream\":
        yield event[\"data\"][\"chunk\"].content
```

#### agno Agent → LangChain 对照表

| agno Agent 功能 | LangChain AgentExecutor | LangGraph |
|-----------------|------------------------|-----------|
| 工具调用 | ✅ 支持 | ✅ 支持 |
| 记忆管理 | ✅ 通过 memory 参数 | ✅ 通过 checkpointer + state |
| 会话摘要 | ❌ 需手动实现 | ❌ 需手动实现 |
| 工具结果压缩 | ❌ 需手动实现 | ❌ 需手动实现 |
| 流式输出 | ✅ stream_events=True | ✅ bstream_events |
| 中断/恢复 | ❌ 不支持 | ✅ 支持人工介入 |
| 循环图 | ❌ 单次执行 | ✅ 任意复杂图 |

__推荐选择__：

- 简单对话（无复杂状态）→ AgentExecutor
- 需要中断/恢复、复杂流程 → LangGraph

---

### 3.3 Memory 替换（步骤 1）

#### 原实现（agno）

```python
from agno.memory import MemoryManager

memory_manager = MemoryManager(
    model=model,
    db=db,
)
```

#### LangChain 替换方案

```python
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import PostgresChatMessageHistory

# 方案 A：简单 Buffer Memory

history = PostgresChatMessageHistory(
    connection_string=\"postgresql://...\",
    session_id=conversation_id,
)

memory = ConversationBufferMemory(
    chat_memory=history,
    memory_key=\"chat_history\",
    return_messages=True,
)

# 方案 B：带摘要的 Memory（类似 agno SessionSummaryManager）

from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(
    llm=model,
    chat_memory=history,
    memory_key=\"chat_history\",
    return_messages=True,
    human_prefix=\"用户\",
    ai_prefix=\"助手\",
)

# 使用

memory.save_context({\"input\": query}, {\"output\": response})
history_messages = memory.load_memory_variables({})
```

---

### 3.4 CompressionManager 替换（步骤 1）

agno 的 CompressionManager 用于压缩工具调用结果，LangChain 无直接对应。

#### 替代方案

```python
from langchain_core.messages import ToolMessage

def compress_tool_results(messages: list, limit: int = 3) -> list:
    \"\"\"压缩工具调用结果，只保留最近 N 条\"\"\"
    compressed = []
    tool_messages_count = 0

    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            tool_messages_count += 1
            if tool_messages_count <= limit:
                compressed.insert(0, msg)
        else:
            compressed.insert(0, msg)
    
    return compressed
```

或直接省略此功能（LangChain 的 ToolMessage 通常较短）。

---

### 3.5 流式事件处理替换（步骤 1）

#### 原实现（agno）

```python
from agno.run.agent import RunEvent, RunOutputEvent

async for response in agent.arun(input=query):
    if response.event == RunEvent.run_content:
        yield {\"event\": \"message\", \"data\": {\"content\": response.content}}
    elif response.event == RunEvent.tool_call_started:
        yield {\"event\": \"search_keywords\", \"data\": {...}}
    elif response.event == RunEvent.run_completed:
        # 提取 metrics
```

#### LangChain 替换方案

```python
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

class StreamingCallbackHandler(AsyncCallbackHandler):
    \"\"\"自定义回调处理器，用于 SSE 事件转换\"\"\"

    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue
    
    async def on_llm_start(self, serialized, prompts, **kwargs):
        await self.event_queue.put({
            \"event\": \"llm_start\",
            \"data\": {\"prompts\": prompts},
        })
    
    async def on_llm_new_token(self, token: str, **kwargs):
        await self.event_queue.put({
            \"event\": \"message\",
            \"data\": {\"content\": token},
        })
    
    async def on_llm_end(self, response: LLMResult, **kwargs):
        usage = response.llm_output.get(\"token_usage\", {})
        await self.event_queue.put({
            \"event\": \"finish\",
            \"data\": {
                \"prompt_tokens\": usage.get(\"prompt_tokens\", 0),
                \"completion_tokens\": usage.get(\"completion_tokens\", 0),
            },
        })
    
    async def on_tool_start(self, serialized, input_str, **kwargs):
        await self.event_queue.put({
            \"event\": \"tool_start\",
            \"data\": {\"tool\": serialized.get(\"name\"), \"input\": input_str},
        })
    
    async def on_tool_end(self, output, **kwargs):
        await self.event_queue.put({
            \"event\": \"tool_end\",
            \"data\": {\"output\": output},
        })

# 使用

callback = StreamingCallbackHandler(event_queue)
async for event in agent_executor.astream_events(
    {\"input\": query},
    version=\"v2\",
    callbacks=[callback],
):
    pass  # 事件由 callback 处理
```

---

### 3.6 数据库持久化替换（步骤 6）

#### 原实现（agno）

```python
from extended.agno.db.postgres.helpers import get_db

db = get_db()  # 返回 AgnoPostgresDb
```

#### LangChain 替换方案

```python
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain_postgres import PGChatMessageHistory

# 方案 A：langchain-community

history = PostgresChatMessageHistory(
    connection_string=\"postgresql://user:pass@host:port/db\",
    session_id=conversation_id,
)

# 方案 B：langchain-postgres（推荐，支持异步）

from langchain_postgres import PostgresChatMessageHistory as AsyncPGHistory

history = AsyncPGHistory(
    async_connection_string=\"postgresql://user:pass@host:port/db\",
    session_id=conversation_id,
)

# 添加消息

await history.aadd_user_message(query)
await history.aadd_ai_message(response)

# 获取历史

messages = await history.aget_messages()
```

---

### 3.7 联网搜索工具替换（步骤 1）

#### 原实现（agno）

```python
from agno.tools.baidusearch import BaiduSearchTools
agent_tools = [BaiduSearchTools()]
```

#### LangChain 替换方案

```python
from langchain_community.tools import BingSearchRun
from langchain.tools import Tool

# 方案 A：使用 BingSearch（需要 Bing API Key）

from langchain_community.utilities import BingSearchAPIWrapper
search = BingSearchAPIWrapper(bing_subscription_key=\"...\", bing_search_url=\"...\")
search_tool = Tool(
    name=\"bing_search\",
    description=\"搜索互联网获取信息\",
    func=search.run,
)

# 方案 B：自定义百度搜索工具

import requests
from langchain.tools import BaseTool

class BaiduSearchTool(BaseTool):
    name = \"baidu_search\"
    description = \"使用百度搜索互联网信息\"

    def _run(self, query: str) -> str:
        # 调用百度搜索 API 或爬虫
        response = requests.get(f\"https://www.baidu.com/s?wd={query}\")
        # 解析结果...
        return result
    
    async def _arun(self, query: str) -> str:
        # 异步实现
        return self._run(query)

agent_tools = [BaiduSearchTool()]
```

---

## 四、控制器层完整替换示例

以下是步骤 1 的完整改造代码框架：

```python

# controllers/portal/v1/generate/llm.py

import asyncio
import uuid
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from <newpkg>.schemas.completion import LLMChatCompletion
from <newpkg>.models.conversation import Conversation, Message
from <newpkg>.components.model.services.llm_service import LLMService
from extended.langchain.models.alon_chat import AlonChatModel
from langchain_core.messages import HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import PostgresChatMessageHistory

router = APIRouter(prefix=\"/apps/llm\", tags=[\"LLM对话\"])

@router.post(\"/chat-messages\")
async def chat_messages(
    chat_completion_in: LLMChatCompletion = Body(...),
) -> StreamingResponse:
    \"\"\"LLM 对话接口（LangChain 版本）\"\"\"

    tenant_id = str(CTX_TENANT_ID.get())
    user_id = str(CTX_USER_ID.get())
    conversation_id = chat_completion_in.conversation_id or str(uuid.uuid4())
    
    # 1. 创建模型
    model = AlonChatModel(
        model=chat_completion_in.model.name,
        provider=chat_completion_in.model.provider,
        tenant_id=tenant_id,
        user_id=user_id,
        model_parameters=chat_completion_in.model.completion_params,
    )
    
    # 2. 创建消息历史
    history = PostgresChatMessageHistory(
        connection_string=settings.database.url,
        session_id=conversation_id,
    )
    
    # 3. 创建 Memory
    memory = ConversationBufferMemory(
        chat_memory=history,
        memory_key=\"chat_history\",
        return_messages=True,
    )
    
    # 4. 准备工具（可选）
    tools = []
    if chat_completion_in.search and chat_completion_in.search.enabled:
        from langchain_community.tools import BingSearchRun
        tools.append(BingSearchRun())
    
    # 5. 创建 Agent
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    
    prompt = ChatPromptTemplate.from_messages([
        (\"system\", \"你是一个有帮助的 AI 助手。\"),
        MessagesPlaceholder(variable_name=\"chat_history\"),
        (\"human\", \"{input}\"),
        MessagesPlaceholder(variable_name=\"agent_scratchpad\"),
    ])
    
    agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
    )
    
    # 6. 流式执行
    event_queue = asyncio.Queue()
    
    async def stream_generator():
        full_content = \"\"
        async for event in agent_executor.astream_events(
            {\"input\": chat_completion_in.query},
            version=\"v2\",
        ):
            if event[\"event\"] == \"on_chat_model_stream\":
                chunk = event[\"data\"][\"chunk\"]
                content = chunk.content
                full_content += content
                yield f\"data: {{```"event```": ```"message```", ```"data```": {{```"content```": ```"{content}```"}}}}\\n\\n\"
            
            elif event[\"event\"] == \"on_chain_end\":
                # 流结束
                yield f\"data: {{```"event```": ```"finish```", ```"data```": {{}}}}\\n\\n\"
        
        # 7. 保存消息到数据库
        await history.aadd_user_message(chat_completion_in.query)
        await history.aadd_ai_message(full_content)
    
    return StreamingResponse(
        stream_generator(),
        media_type=\"text/event-stream\",
    )
```

---

## 五、迁移步骤调整

替换 agno 后，原迁移文档的步骤需调整：

### 新增步骤：6-LC（LangChain 桥接）

__插入位置__：原步骤 6（Agno 桥接）替换为新步骤 6-LC

```
步骤 4: 通用基础设施
    ↓
步骤 9: Plugin SDK
    ↓
步骤 8: Plugin 组件
    ↓
步骤 7: Model 组件
    ↓
步骤 6-LC: LangChain 桥接（新增）
    ↓
步骤 5: 后台任务管控
    ↓
步骤 3: Models（ORM）
    ↓
步骤 2: Schemas
    ↓
步骤 1: 控制器层
```

### 步骤 6-LC 文件清单

```
extended/langchain/
├── models/
│   ├── alon_chat.py              # 【核心】AlonChatModel 实现
│   └── __init__.py
├── agents/
│   ├── agent_factory.py          # Agent 创建工厂（可选）
│   └── __init__.py
└── __init__.py
```

### 可删除的 agno 相关代码

```
extended/agno/                     # 整个目录可删除
alon/utils/agno_util.py           # extract_usage_from_agent 不再需要
```

---

## 六、功能对比与取舍

| 功能 | agno 原生支持 | LangChain 支持 | 是否需要自行实现 |
|------|--------------|----------------|-----------------|
| 流式对话 | ✅ | ✅ | 否 |
| 工具调用 | ✅ | ✅ | 否 |
| 记忆管理 | ✅ MemoryManager | ✅ ConversationBufferMemory | 否 |
| 会话摘要 | ✅ SessionSummaryManager | ⚠️ ConversationSummaryMemory | 需适配 |
| 工具结果压缩 | ✅ CompressionManager | ❌ | 可选实现 |
| 会话名称生成 | ✅ agenerate_session_name | ❌ | 需自行实现 |
| 数据库持久化 | ✅ AgnoPostgresDb | ✅ PostgresChatMessageHistory | 否 |
| 多模态（图片） | ✅ agno.media.Image | ⚠️ 需手动处理 | 需适配 |

---

## 七、验证清单（LangChain 版本）

- [ ] AlonChatModel.ainvoke 正确返回 ChatResult
- [ ] AlonChatModel._astream 正确流式返回 ChatGenerationChunk
- [ ] AgentExecutor 能正确调用工具
- [ ] PostgresChatMessageHistory 正确持久化消息
- [ ] bstream_events 正确产生流式事件
- [ ] SSE 格式与前端兼容
- [ ] Token 使用统计正确

---

## 八、参考资料

### LangChain 官方文档

- 自定义 ChatModel：<https://python.langchain.com/docs/how_to/custom_chat_model/>
- AgentExecutor：<https://python.langchain.com/docs/modules/agents/>
- LangGraph：<https://langchain-ai.github.io/langgraph/>
- 消息历史：<https://python.langchain.com/docs/modules/memory/chat_messages/>

### agno 对比参考

- agno GitHub：<https://github.com/agno-agi/agno>
- agno 文档：<https://docs.agno.com/>
