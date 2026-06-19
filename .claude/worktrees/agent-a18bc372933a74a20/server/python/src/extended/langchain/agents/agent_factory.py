"""
AgentFactory - Simplifies creation of LangGraph agents

Provides factory methods to create agents and custom
LangGraph workflows using the AlonChatModel.
"""

from __future__ import annotations

from typing import Annotated, Any

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from extended.langchain.models.alon_chat import AlonChatModel


class AgentState(TypedDict):
    """State schema for custom agent graphs."""

    messages: Annotated[list, add_messages]


class AgentFactory:
    """Factory for creating LangGraph agents with AlonChatModel."""

    def __init__(self, model: AlonChatModel) -> None:
        self.model = model

    def create_executor(
        self,
        tools: list | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        prompt: str | SystemMessage | None = None,
    ) -> CompiledStateGraph:
        """Create an agent using langchain create_agent."""
        kwargs: dict[str, Any] = {"model": self.model}
        if tools:
            kwargs["tools"] = tools
        if checkpointer:
            kwargs["checkpointer"] = checkpointer
        if prompt:
            kwargs["system_prompt"] = prompt
        return create_agent(**kwargs)

    def create_graph(
        self,
        tools: list,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> CompiledStateGraph:
        """Create a custom LangGraph with tool-calling loop."""
        tool_node = ToolNode(tools)

        async def call_model(state: AgentState) -> dict:
            response = await self.model.ainvoke(state["messages"])
            return {"messages": [response]}

        def should_continue(state: AgentState) -> str:
            messages = state["messages"]
            last_message = messages[-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "end"

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent", should_continue, {"tools": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")

        compile_kwargs: dict[str, Any] = {}
        if checkpointer:
            compile_kwargs["checkpointer"] = checkpointer
        return workflow.compile(**compile_kwargs)
