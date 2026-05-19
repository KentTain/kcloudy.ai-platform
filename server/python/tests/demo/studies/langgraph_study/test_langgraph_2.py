"""LangGraph 条件路由测试

演示如何使用条件边（conditional_edges）进行动态路由。

核心概念：
- add_conditional_edges: 根据状态动态选择下一个节点
- 路由函数: 返回下一个节点的键名
- 条件映射: 将路由结果映射到具体节点
"""

import logging
from dataclasses import dataclass
from operator import add
from typing import Annotated, Literal

import pytest

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

_logger = logging.getLogger(__name__)


@dataclass
class GraphState:
    """图状态"""

    result: Annotated[list[str], add]
    route_decision: str = ""


def start_node(state: GraphState) -> GraphState:
    """起始节点"""
    print(f"\n[Start] 开始处理")
    return GraphState(result=["start"], route_decision=state.route_decision)


def path_a_node(state: GraphState) -> GraphState:
    """路径A"""
    print(f"\n[Path A] 执行路径A")
    return GraphState(result=["path_a"], route_decision=state.route_decision)


def path_b_node(state: GraphState) -> GraphState:
    """路径B"""
    print(f"\n[Path B] 执行路径B")
    return GraphState(result=["path_b"], route_decision=state.route_decision)


def end_node(state: GraphState) -> GraphState:
    """结束节点"""
    print(f"\n[End] 处理完成")
    return GraphState(result=["end"], route_decision=state.route_decision)


def route_function(state: GraphState) -> Literal["go_a", "go_b"]:
    """路由函数：根据状态决定下一个节点

    返回值对应 add_conditional_edges 的 path_map 键
    """
    decision = state.route_decision
    print(f"\n[Router] 路由决策: {decision}")

    if decision == "a":
        return "go_a"
    else:
        return "go_b"


def build_graph() -> CompiledStateGraph:
    """构建带条件边的图"""
    graph = StateGraph(state_schema=GraphState)

    # 添加节点
    graph.add_node(node="start", action=start_node)
    graph.add_node(node="path_a", action=path_a_node)
    graph.add_node(node="path_b", action=path_b_node)
    graph.add_node(node="end", action=end_node)

    # 设置入口点
    graph.set_entry_point(key="start")

    # 条件边：从 start 根据路由函数选择 path_a 或 path_b
    graph.add_conditional_edges(
        source="start",
        path=route_function,
        path_map={
            "go_a": "path_a",
            "go_b": "path_b",
        },
    )

    # 普通边：path_a 和 path_b 都指向 end
    graph.add_edge(start_key="path_a", end_key="end")
    graph.add_edge(start_key="path_b", end_key="end")

    # 设置结束点
    graph.set_finish_point(key="end")

    return graph.compile()


@pytest.fixture
def graph() -> CompiledStateGraph:
    return build_graph()


@pytest.mark.asyncio
async def test_route_to_path_a(graph: CompiledStateGraph):
    """测试路由到路径A"""
    print("\n" + "=" * 60)
    print("测试：路由到路径A")
    print("=" * 60)

    initial_state = {"result": [], "route_decision": "a"}
    result = await graph.ainvoke(initial_state)

    print(f"\n最终结果: {result['result']}")

    assert "start" in result["result"]
    assert "path_a" in result["result"]
    assert "path_b" not in result["result"]
    assert "end" in result["result"]


@pytest.mark.asyncio
async def test_route_to_path_b(graph: CompiledStateGraph):
    """测试路由到路径B"""
    print("\n" + "=" * 60)
    print("测试：路由到路径B")
    print("=" * 60)

    initial_state = {"result": [], "route_decision": "b"}
    result = await graph.ainvoke(initial_state)

    print(f"\n最终结果: {result['result']}")

    assert "start" in result["result"]
    assert "path_b" in result["result"]
    assert "path_a" not in result["result"]
    assert "end" in result["result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
