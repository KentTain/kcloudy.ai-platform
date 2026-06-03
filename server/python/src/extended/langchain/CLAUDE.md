# extended/langchain

LangChain bridge layer - connects LangChain ecosystem to platform LLMService.

## Modules

| Module | Description |
|--------|-------------|
| models/alon_chat.py | AlonChatModel - BaseChatModel bridge to LLMService |
| models/message_adapter.py | MessageAdapter - BaseMessage <-> PromptMessage converter |
| agents/agent_factory.py | AgentFactory - create_agent / custom LangGraph builder |

## Key APIs

`python
from extended.langchain import AlonChatModel, MessageAdapter, AgentFactory

# Create model

model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")

# Non-streaming call

result = await model.ainvoke([HumanMessage(content="Hello")])

# Streaming call

async for chunk in model.astream([HumanMessage(content="Hello")]):
    print(chunk.content)

# Create agent

factory = AgentFactory(model=model)
agent = factory.create_executor(tools=[search_tool])
result = await agent.ainvoke({"messages": [HumanMessage(content="Hello")]})
`

## Dependencies

- langchain[community]==1.3.0 (uses langchain.agents.create_agent)
- langgraph (StateGraph, ToolNode, MemorySaver)
- ai.components.model.services.llm_service.LLMService
- ai_plugin.sdk.entities.model (PromptMessage, LLMResult, LLMResultChunk)

## Testing

`bash
uv run pytest tests/extended/langchain/ -v
`
