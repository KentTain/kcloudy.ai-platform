"""AgentFactory unit tests"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from extended.langchain.models.alon_chat import AlonChatModel
from extended.langchain.agents.agent_factory import AgentFactory


@tool
def dummy_search(query: str) -> str:
    """Search the web."""
    return f"Result for {query}"


def _make_model() -> AlonChatModel:
    return AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")


class TestAgentFactoryInit:
    def test_factory_binds_model(self):
        model = _make_model()
        factory = AgentFactory(model=model)
        assert factory.model is model


class TestCreateExecutor:
    def test_creates_compiled_graph(self):
        factory = AgentFactory(model=_make_model())
        executor = factory.create_executor(tools=[dummy_search])
        assert isinstance(executor, CompiledStateGraph)

    def test_with_checkpointer(self):
        factory = AgentFactory(model=_make_model())
        checkpointer = MemorySaver()
        executor = factory.create_executor(
            tools=[dummy_search], checkpointer=checkpointer
        )
        assert isinstance(executor, CompiledStateGraph)

    def test_with_prompt(self):
        factory = AgentFactory(model=_make_model())
        executor = factory.create_executor(
            tools=[dummy_search],
            prompt="You are a helpful assistant.",
        )
        assert isinstance(executor, CompiledStateGraph)

    def test_no_tools(self):
        factory = AgentFactory(model=_make_model())
        executor = factory.create_executor(tools=[])
        assert isinstance(executor, CompiledStateGraph)


class TestCreateGraph:
    def test_creates_custom_graph(self):
        factory = AgentFactory(model=_make_model())
        graph = factory.create_graph(tools=[dummy_search])
        assert isinstance(graph, CompiledStateGraph)

    def test_with_checkpointer(self):
        factory = AgentFactory(model=_make_model())
        checkpointer = MemorySaver()
        graph = factory.create_graph(tools=[dummy_search], checkpointer=checkpointer)
        assert isinstance(graph, CompiledStateGraph)
