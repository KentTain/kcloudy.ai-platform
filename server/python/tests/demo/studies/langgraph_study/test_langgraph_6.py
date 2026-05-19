"""LangGraph 条件路由示例

演示如何使用 LangGraph 实现条件分支和路由。

## 核心概念

### 1. 条件路由
- **条件边**：根据状态值动态选择下一个节点
- **路由函数**：返回目标节点名称的函数
- **path_map**：路由结果到目标节点的映射

### 2. 工作流程

START -> node1 -> condition_node2 -> [node3_a (true) | node3_b (false)] -> node4 -> END

### 3. 关键特性

#### 状态驱动的路由决策
- 节点更新状态中的条件字段
- 路由函数根据状态值决定执行路径
- 条件边使用 `add_conditional_edges` 定义
"""

import uuid
from dataclasses import dataclass
from operator import add
from typing import Annotated, Any

import pytest
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


@dataclass
class GraphRuntimeState:
    """图运行状态"""

    result: Annotated[list[str], add]
    execution_index: Annotated[list[int], add]
    condition_value: int = 0


@dataclass
class GraphInput:
    """图输入"""

    result: list[str]
    execution_index: list[int]


@dataclass
class GraphOutput:
    """图输出"""

    result: list[str]
    execution_index: list[int]


# 全局执行计数器
_execution_counter = 0


def get_next_index() -> int:
    """获取下一个执行索引"""
    global _execution_counter
    _execution_counter += 1
    return _execution_counter


def reset_counter():
    """重置计数器"""
    global _execution_counter
    _execution_counter = 0


def node1_func(state: GraphRuntimeState) -> dict[str, Any]:
    """节点1处理函数"""
    current_index = get_next_index()
    print(f"[Node 1] index: {current_index}, state: {state.result}")

    return {
        "result": ["node1"],
        "execution_index": [current_index],
    }


def condition_node2_func(state: GraphRuntimeState) -> dict[str, Any]:
    """条件节点处理函数"""
    current_index = get_next_index()

    import random

    condition_value = random.randint(0, 1)

    print(
        f"[Condition Node 2] index: {current_index}, state: {state.result}, "
        f"condition_value: {condition_value}"
    )

    return {
        "result": ["condition_node2"],
        "execution_index": [current_index],
        "condition_value": condition_value,
    }


def node3_a_func(state: GraphRuntimeState) -> dict[str, Any]:
    """节点3 A处理函数"""
    current_index = get_next_index()
    print(f"[Node 3 A] index: {current_index}, state: {state.result}")

    return {
        "result": ["node3_a"],
        "execution_index": [current_index],
    }


def node3_b_func(state: GraphRuntimeState) -> dict[str, Any]:
    """节点3 B处理函数"""
    current_index = get_next_index()
    print(f"[Node 3 B] index: {current_index}, state: {state.result}")

    return {
        "result": ["node3_b"],
        "execution_index": [current_index],
    }


def node4_func(state: GraphRuntimeState) -> dict[str, Any]:
    """节点4处理函数"""
    current_index = get_next_index()
    print(f"[Node 4] index: {current_index}, state: {state.result}")

    return {
        "result": ["node4"],
        "execution_index": [current_index],
    }


def condition_node2_router(state: GraphRuntimeState) -> str:
    """条件路由函数：根据状态决定下一步路径"""
    condition_value = state.condition_value

    if condition_value == 0:
        print("[Router] condition_value=0 -> true branch")
        return "true"
    else:
        print("[Router] condition_value=1 -> false branch")
        return "false"


def build_graph() -> CompiledStateGraph:
    """构建条件路由状态图"""
    graph = StateGraph(
        state_schema=GraphRuntimeState,
        input_schema=GraphInput,
        output_schema=GraphOutput,
    )

    # 添加节点
    graph.add_node(node="node1", action=node1_func)
    graph.add_node(node="condition_node2", action=condition_node2_func)
    graph.add_node(node="node3_a", action=node3_a_func)
    graph.add_node(node="node3_b", action=node3_b_func)
    graph.add_node(node="node4", action=node4_func)

    # 设置边 - 实现条件分支结构
    graph.add_edge(start_key=START, end_key="node1")
    graph.add_edge(start_key="node1", end_key="condition_node2")

    # 条件边：根据condition_value决定路径
    graph.add_conditional_edges(
        source="condition_node2",
        path=condition_node2_router,
        path_map={
            "true": "node3_a",  # 条件为True到node3_a
            "false": "node3_b",  # 条件为False到node3_b
        },
    )

    graph.add_edge(start_key="node3_a", end_key="node4")
    graph.add_edge(start_key="node3_b", end_key="node4")
    graph.add_edge(start_key="node4", end_key=END)

    return graph.compile()


@pytest.fixture
def graph():
    """创建图 fixture"""
    reset_counter()
    return build_graph()


@pytest.mark.asyncio
async def test_graph_execution(graph):
    """测试图的执行"""

    config = RunnableConfig(
        run_id=uuid.uuid4(),
    )

    # 初始化状态
    input_data = GraphInput(
        result=[],
        execution_index=[],
    )

    print("\n开始执行图\n")

    # 执行图
    result = await graph.ainvoke(
        input=input_data,
        config=config,
    )

    print(f"\n[Final] result: {result['result']}")
    print(f"[Final] execution_index: {result['execution_index']}")
    print(f"[Final] condition_value: {result.get('condition_value', 'N/A')}")

    # 验证执行结果
    assert "node1" in result["result"]
    assert "condition_node2" in result["result"]
    assert "node4" in result["result"]
    # 应该走了其中一个分支
    assert ("node3_a" in result["result"]) or ("node3_b" in result["result"])


def condition_node_true(state: GraphRuntimeState) -> dict[str, Any]:
    """强制设置为 true 分支的条件节点"""
    return {
        "result": ["condition_node2"],
        "execution_index": [],
        "condition_value": 0,
    }


def condition_node_false(state: GraphRuntimeState) -> dict[str, Any]:
    """强制设置为 false 分支的条件节点"""
    return {
        "result": ["condition_node2"],
        "execution_index": [],
        "condition_value": 1,
    }


@pytest.mark.asyncio
async def test_conditional_routing_true_branch():
    """测试条件路由走 true 分支"""
    reset_counter()

    # 构建一个强制走 true 分支的图
    def always_true_router(state: GraphRuntimeState) -> str:
        return "true"

    graph_builder = StateGraph(
        state_schema=GraphRuntimeState,
        input_schema=GraphInput,
        output_schema=GraphOutput,
    )

    graph_builder.add_node(node="node1", action=node1_func)
    graph_builder.add_node(node="condition_node2", action=condition_node_true)
    graph_builder.add_node(node="node3_a", action=node3_a_func)
    graph_builder.add_node(node="node3_b", action=node3_b_func)
    graph_builder.add_node(node="node4", action=node4_func)

    graph_builder.add_edge(START, "node1")
    graph_builder.add_edge("node1", "condition_node2")
    graph_builder.add_conditional_edges(
        "condition_node2",
        always_true_router,
        {"true": "node3_a", "false": "node3_b"},
    )
    graph_builder.add_edge("node3_a", "node4")
    graph_builder.add_edge("node3_b", "node4")
    graph_builder.add_edge("node4", END)

    graph = graph_builder.compile()

    result = await graph.ainvoke(GraphInput(result=[], execution_index=[]))

    print(f"\n[Final] result: {result['result']}")
    assert "node3_a" in result["result"]
    assert "node3_b" not in result["result"]


@pytest.mark.asyncio
async def test_conditional_routing_false_branch():
    """测试条件路由走 false 分支"""
    reset_counter()

    # 构建一个强制走 false 分支的图
    def always_false_router(state: GraphRuntimeState) -> str:
        return "false"

    graph_builder = StateGraph(
        state_schema=GraphRuntimeState,
        input_schema=GraphInput,
        output_schema=GraphOutput,
    )

    graph_builder.add_node(node="node1", action=node1_func)
    graph_builder.add_node(node="condition_node2", action=condition_node_false)
    graph_builder.add_node(node="node3_a", action=node3_a_func)
    graph_builder.add_node(node="node3_b", action=node3_b_func)
    graph_builder.add_node(node="node4", action=node4_func)

    graph_builder.add_edge(START, "node1")
    graph_builder.add_edge("node1", "condition_node2")
    graph_builder.add_conditional_edges(
        "condition_node2",
        always_false_router,
        {"true": "node3_a", "false": "node3_b"},
    )
    graph_builder.add_edge("node3_a", "node4")
    graph_builder.add_edge("node3_b", "node4")
    graph_builder.add_edge("node4", END)

    graph = graph_builder.compile()

    result = await graph.ainvoke(GraphInput(result=[], execution_index=[]))

    print(f"\n[Final] result: {result['result']}")
    assert "node3_b" in result["result"]
    assert "node3_a" not in result["result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
