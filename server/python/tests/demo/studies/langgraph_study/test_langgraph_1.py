"""LangGraph 基础状态图测试

演示如何构建和执行一个简单的 LangGraph 状态图。

核心概念：
- State: 图的状态，在节点间传递
- Node: 处理节点，接收状态，返回更新的状态
- Edge: 有向边，定义执行流程

注意：由于 langchain/langchain_core 版本兼容性问题，
需要在导入 langgraph 前设置 debug 属性。
"""

import logging
from dataclasses import dataclass
from operator import add
from typing import Annotated

import pytest

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

_logger = logging.getLogger(__name__)


@dataclass
class GraphState:
    """图运行状态 - 在节点间传递和累积的状态

    使用 Annotated + add 表示该字段是累积型的，
    每个节点的返回值会被追加到现有状态上。
    """

    result: Annotated[list[str], add]
    user_id: str = ""


def node1_func(state: GraphState) -> GraphState:
    """节点1处理函数"""
    print(f"\n[Node 1] state: {state.result}, user_id: {state.user_id}")
    return GraphState(result=["node1"], user_id=state.user_id)


def node2_func(state: GraphState) -> GraphState:
    """节点2处理函数"""
    print(f"\n[Node 2] state: {state.result}, user_id: {state.user_id}")
    return GraphState(result=["node2"], user_id=state.user_id)


def node3_func(state: GraphState) -> GraphState:
    """节点3处理函数"""
    print(f"\n[Node 3] state: {state.result}, user_id: {state.user_id}")
    return GraphState(result=["node3"], user_id=state.user_id)


def build_graph() -> CompiledStateGraph:
    """构建简单的状态图

    构建流程：
    1. 创建 StateGraph 实例，指定状态 schema
    2. 添加节点（node）
    3. 定义边（edge）连接节点
    4. 设置入口点和结束点
    5. 编译图
    """
    # 创建图
    graph = StateGraph(state_schema=GraphState)

    # 添加节点
    graph.add_node(node="node1", action=node1_func)
    graph.add_node(node="node2", action=node2_func)
    graph.add_node(node="node3", action=node3_func)

    # 设置边：定义执行流程 node1 -> node2 -> node3
    graph.add_edge(start_key="node1", end_key="node2")
    graph.add_edge(start_key="node2", end_key="node3")

    # 设置入口点和结束点
    graph.set_entry_point(key="node1")
    graph.set_finish_point(key="node3")

    # 编译图
    return graph.compile()


@pytest.fixture
def graph() -> CompiledStateGraph:
    """创建图 fixture"""
    return build_graph()


@pytest.mark.asyncio
async def test_graph_run(graph: CompiledStateGraph):
    """测试图异步执行

    演示基本的图构建和执行流程。
    """
    print("\n" + "=" * 60)
    print("测试 LangGraph 基础状态图执行")
    print("=" * 60)

    # 初始化状态
    initial_state = {"result": [], "user_id": "demo_user_123"}

    print("\n开始执行图...")

    # 执行图
    result = await graph.ainvoke(initial_state)

    # 打印结果
    print(f"\n执行完成！最终结果: {result['result']}")

    # 验证结果（由于使用 Annotated + add，结果应该包含所有节点的输出）
    assert "node1" in result["result"]
    assert "node2" in result["result"]
    assert "node3" in result["result"]


@pytest.mark.asyncio
async def test_graph_with_initial_state(graph: CompiledStateGraph):
    """测试带初始状态的图执行"""
    print("\n" + "=" * 60)
    print("测试带初始状态的图执行")
    print("=" * 60)

    # 提供包含初始数据的输入状态
    initial_state = {"result": ["initial_data"], "user_id": "test_user"}

    result = await graph.ainvoke(initial_state)

    print(f"\n初始状态: ['initial_data']")
    print(f"最终结果: {result['result']}")

    # 验证初始状态被保留，且节点输出被追加
    assert "initial_data" in result["result"]
    assert "node1" in result["result"]


@pytest.mark.asyncio
async def test_graph_sync_invoke(graph: CompiledStateGraph):
    """测试图同步执行"""
    print("\n" + "=" * 60)
    print("测试 LangGraph 同步执行")
    print("=" * 60)

    initial_state = {"result": [], "user_id": "sync_user"}

    # 同步执行
    result = graph.invoke(initial_state)

    print(f"\n执行完成！最终结果: {result['result']}")

    assert len(result["result"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
