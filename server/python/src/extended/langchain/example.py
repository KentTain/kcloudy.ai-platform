"""
LangChain bridge usage example

Demonstrates how to use AlonChatModel, MessageAdapter, and AgentFactory
to integrate LangChain with the platform LLMService.
"""

from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from extended.langchain import AgentFactory, AlonChatModel, MessageAdapter


async def demo_alon_chat_model() -> None:
    """Demo: non-streaming and streaming calls with AlonChatModel."""
    model = AlonChatModel(
        model="gpt-4",
        provider="openai",
        tenant_id="demo-tenant",
        model_parameters={"temperature": 0.7},
    )

    # Non-streaming
    result = await model.ainvoke(
        [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello!"),
        ]
    )
    print(f"Response: {result.content}")

    # Streaming
    print("Streaming: ", end="")
    async for chunk in model.astream([HumanMessage(content="Tell me a joke")]):
        print(chunk.content, end="", flush=True)
    print()


async def demo_message_adapter() -> None:
    """Demo: bidirectional message conversion."""
    # LangChain -> Platform
    lc_msg = HumanMessage(content="Hello")
    platform_msg = MessageAdapter.to_platform_message(lc_msg)
    print(f"Platform message role: {platform_msg.role.value}")

    # Platform -> LangChain
    back = MessageAdapter.to_langchain_message(platform_msg)
    print(f"Back to LangChain: {back.type} = {back.content}")


async def demo_agent_factory() -> None:
    """Demo: creating agents with AgentFactory."""
    model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="demo-tenant")
    factory = AgentFactory(model=model)

    @tool
    def search(query: str) -> str:
        """Search the web."""
        return f"Result for: {query}"

    # Simple agent
    agent = factory.create_executor(
        tools=[search],
        prompt="You are a helpful assistant with search capability.",
    )
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="Search for Python tutorials")]},
    )
    print(f"Agent result: {result}")

    # Agent with checkpointer
    checkpointer = MemorySaver()
    agent_with_memory = factory.create_executor(
        tools=[search],
        checkpointer=checkpointer,
    )
    config = {"configurable": {"thread_id": "session-1"}}
    result1 = await agent_with_memory.ainvoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config,
    )
    print(f"With memory: {result1}")


if __name__ == "__main__":
    asyncio.run(demo_message_adapter())
