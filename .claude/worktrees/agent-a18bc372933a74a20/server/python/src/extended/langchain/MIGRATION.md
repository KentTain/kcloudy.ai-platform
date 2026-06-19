# Agno -> LangChain Migration Notes

## What was migrated

| Agno Component | LangChain Equivalent | Status |
|----------------|---------------------|--------|
| agno.models.base.Model | BaseChatModel (AlonChatModel) | Done |
| agno.models.message.Message | langchain_core.messages.BaseMessage via MessageAdapter | Done |
| agno.agent.Agent | langchain.agents.create_agent via AgentFactory | Done |
| agno.memory.MemoryManager | LangGraph checkpointer | Not migrated (use langgraph checkpointer directly) |
| agno.utils.message_utils | MessageAdapter | Done |

## What was NOT migrated

- CompressionManager - LangChain has no direct equivalent; tool result compression can be implemented per-need
- SessionSummaryManager - Use ConversationSummaryMemory or custom implementation
- AgnoPostgresDb - Use langgraph.checkpoint.postgres or langchain_postgres instead
- BaiduSearchTools - Use langchain_community.tools or custom BaseTool

## API Differences

| Aspect | Agno | LangChain |
|--------|------|-----------|
| Agent creation | Agent(model=..., tools=[...]) | create_agent(model, tools=[...]) |
| Streaming | agent.arun(stream=True) | model.astream() / agent.astream() |
| Memory | MemoryManager(db=db) | MemorySaver / AsyncPostgresSaver |
| Events | RunEvent.run_content | astream_events(version="v2") |
