"""LangGraph 汇聚点测试

演示如何处理多个节点汇聚到一个节点的情况。

核心概念：
- 多起点边: 使用列表作为 add_edge 的 start_key
- 汇聚节点: 等待所有上游节点完成后执行一次

问题场景：
- 错误方式：多个独立 add_edge 导致汇聚节点多次执行
- 正确方式：使用列表语法或 defer=True
"""

import logging
from dataclasses import dataclass
from operator import add
from typing import Annotated

import pytest
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

_logger = logging.getLogger(__name__)


@dataclass
class GraphState:
    """图状态"""

    result: Annotated[list[str], add]
    execution_count: Annotated[list[int], add]


def source_node_a(state: GraphState) -> GraphState:
    """源节点A"""
    print("\n[Source A] 执行")
    return GraphState(result=["source_a"], execution_count=[1])


def source_node_b(state: GraphState) -> GraphState:
    """源节点B"""
    print("\n[Source B] 执行")
    return GraphState(result=["source_b"], execution_count=[1])


def source_node_c(state: GraphState) -> GraphState:
    """源节点C"""
    print("\n[Source C] 执行")
    return GraphState(result=["source_c"], execution_count=[1])


def converge_node(state: GraphState) -> GraphState:
    """汇聚节点 - 应该只执行一次"""
    current_count = len(state.execution_count)
    print(f"\n[Converge] 汇聚执行 - 当前计数: {current_count}")
    return GraphState(result=["converge"], execution_count=[1])


def final_node(state: GraphState) -> GraphState:
    """最终节点"""
    print("\n[Final] 最终执行")
    return GraphState(result=["final"], execution_count=[1])


def build_correct_graph() -> CompiledStateGraph:
    """构建正确的汇聚图：使用多起点边语法

    关键：使用列表语法 ["source_a", "source_b"] 作为 start_key
    这表示 converge 需要等待 source_a 和 source_b 都完成
    """
    graph = StateGraph(state_schema=GraphState)

    # 添加节点
    graph.add_node(node="source_a", action=source_node_a)
    graph.add_node(node="source_b", action=source_node_b)
    graph.add_node(node="source_c", action=source_node_c)
    graph.add_node(node="converge", action=converge_node)
    graph.add_node(node="final", action=final_node)

    # 入口点指向多个并行节点
    graph.add_edge(START, "source_a")
    graph.add_edge(START, "source_b")
    graph.add_edge(START, "source_c")

    # 正确方式：使用列表语法进行汇聚
    # converge 等待 source_a, source_b, source_c 都完成
    graph.add_edge(["source_a", "source_b", "source_c"], "converge")

    # 结束边
    graph.add_edge("converge", "final")
    graph.add_edge("final", END)

    return graph.compile()


@pytest.fixture
def correct_graph() -> CompiledStateGraph:
    return build_correct_graph()


@pytest.mark.asyncio
async def test_correct_convergence(correct_graph: CompiledStateGraph):
    """测试正确的汇聚行为

    验证：
    1. 所有源节点都执行
    2. 汇聚节点只执行一次
    3. 最终节点正常执行
    """
    print("\n" + "=" * 60)
    print("测试：正确的汇聚行为（多起点边）")
    print("=" * 60)

    initial_state = {"result": [], "execution_count": []}
    result = await correct_graph.ainvoke(initial_state)

    print(f"\n最终结果: {result['result']}")
    print(f"执行计数: {len(result['execution_count'])}")

    # 验证所有源节点都执行
    assert "source_a" in result["result"]
    assert "source_b" in result["result"]
    assert "source_c" in result["result"]

    # 验证汇聚节点只执行一次
    converge_count = result["result"].count("converge")
    print(f"\n汇聚节点执行次数: {converge_count}")
    assert converge_count == 1, (
        f"汇聚节点应该只执行一次，实际执行了 {converge_count} 次"
    )

    # 验证最终节点执行
    assert "final" in result["result"]


@pytest.mark.asyncio
async def test_parallel_execution(correct_graph: CompiledStateGraph):
    """测试并行执行

    验证源节点是并行执行的（通过执行顺序推断）
    """
    print("\n" + "=" * 60)
    print("测试：并行执行验证")
    print("=" * 60)

    initial_state = {"result": [], "execution_count": []}
    result = await correct_graph.ainvoke(initial_state)

    # 源节点应该出现在汇聚节点之前
    result_str = str(result["result"])
    print(f"\n执行顺序: {result['result']}")

    # 验证基本顺序
    assert result["result"].index("source_a") < result["result"].index("converge")
    assert result["result"].index("source_b") < result["result"].index("converge")
    assert result["result"].index("source_c") < result["result"].index("converge")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
