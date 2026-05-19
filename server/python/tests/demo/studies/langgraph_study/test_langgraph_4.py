"""LangGraph 子图示例

演示如何使用 LangGraph 创建和使用子图（subgraphs）。

## 核心概念

### 1. 基本子图概念
- **子图**：一个完整的图，可以作为父图中的一个节点
- **状态管理**：子图和父图之间可以共享状态或使用不同的状态架构
- **模块化**：子图提供了工作流的模块化和重用能力

### 2. 工作流程

#### 基本子图执行流程
START -> process -> validate -> finalize -> END

#### 父图调用子图流程
START -> init -> call_subgraph -> finalize -> END
              ↓
      子图: process -> validate -> finalize

### 3. 关键特性

#### 状态共享
- 使用 `Annotated[List[str], add]` 实现状态累加
- 子图和父图可以共享相同的状态字段

#### 状态转换
- 当子图和父图使用不同状态架构时
- 需要在调用子图前后进行状态转换
"""

import functools
from dataclasses import dataclass
from operator import add
from typing import Annotated

import pytest
from langgraph.graph import StateGraph
from langgraph.graph.state import START, CompiledStateGraph


@dataclass
class GraphContext:
    """图的上下文信息"""

    user_id: str


# 子图状态定义
@dataclass
class SubgraphRuntimeState:
    """子图运行状态"""

    # 与父图共享的状态字段
    shared_data: Annotated[list[str], add]
    # 子图私有的状态字段
    private_data: str


# 父图状态定义
@dataclass
class ParentGraphRuntimeState:
    """父图运行状态"""

    # 与子图共享的状态字段
    shared_data: Annotated[list[str], add]
    # 父图私有的状态字段
    parent_info: str


# 子图的输入输出定义
@dataclass
class SubgraphInput:
    """子图输入"""

    shared_data: list[str]
    private_data: str


@dataclass
class SubgraphOutput:
    """子图输出"""

    shared_data: list[str]
    private_data: str


# 父图的输入输出定义
@dataclass
class ParentGraphInput:
    """父图输入"""

    shared_data: list[str]
    parent_info: str


@dataclass
class ParentGraphOutput:
    """父图输出"""

    shared_data: list[str]
    parent_info: str


# 子图节点函数
def subgraph_process_node(
    state: SubgraphRuntimeState, processing_step: str
) -> SubgraphRuntimeState:
    """子图处理节点"""
    print(f"subgraph process -> state: {state.shared_data}, step: {processing_step}")

    return SubgraphRuntimeState(
        shared_data=[f"subgraph_{processing_step}_processed"],
        private_data=f"private_{processing_step}_data",
    )


def subgraph_validate_node(state: SubgraphRuntimeState) -> SubgraphRuntimeState:
    """子图验证节点"""
    print(
        f"subgraph validate -> state: {state.shared_data}, private: {state.private_data}"
    )

    return SubgraphRuntimeState(
        shared_data=["validation_passed"],
        private_data="validation_complete",
    )


def subgraph_finalize_node(state: SubgraphRuntimeState) -> SubgraphRuntimeState:
    """子图完成节点"""
    print(
        f"subgraph finalize -> state: {state.shared_data}, private: {state.private_data}"
    )

    return SubgraphRuntimeState(
        shared_data=["subgraph_finalized"],
        private_data="finalize_complete",
    )


# 父图节点函数
def parent_init_node(state: ParentGraphRuntimeState) -> ParentGraphRuntimeState:
    """父图初始化节点"""
    print(f"parent init -> state: {state.shared_data}, parent: {state.parent_info}")

    return ParentGraphRuntimeState(
        shared_data=["parent_initialized"],
        parent_info="initialization_complete",
    )


def parent_call_subgraph_node(
    state: ParentGraphRuntimeState,
    subgraph: CompiledStateGraph,
) -> ParentGraphRuntimeState:
    """父图调用子图节点"""
    print(
        f"parent call subgraph -> state: {state.shared_data}, parent: {state.parent_info}"
    )

    # 构造子图输入，状态转换
    subgraph_input = SubgraphInput(
        shared_data=state.shared_data, private_data="from_parent"
    )

    # 调用子图
    subgraph_result = subgraph.invoke(input=subgraph_input)

    # 将子图结果合并回父图状态
    return ParentGraphRuntimeState(
        shared_data=state.shared_data + subgraph_result["shared_data"],
        parent_info=f"{state.parent_info}_after_subgraph",
    )


def parent_final_node(state: ParentGraphRuntimeState) -> ParentGraphRuntimeState:
    """父图最终节点"""
    print(f"parent final -> state: {state.shared_data}, parent: {state.parent_info}")

    return ParentGraphRuntimeState(
        shared_data=["parent_completed"],
        parent_info="workflow_complete",
    )


# 构建子图
def build_subgraph() -> CompiledStateGraph:
    """构建子图"""
    subgraph = StateGraph(
        state_schema=SubgraphRuntimeState,
        input_schema=SubgraphInput,
        output_schema=SubgraphOutput,
    )

    # 添加子图节点
    subgraph.add_node(
        node="process",
        action=functools.partial(
            subgraph_process_node,
            processing_step="data_transformation",
        ),
    )
    subgraph.add_node(
        node="validate",
        action=subgraph_validate_node,
    )
    subgraph.add_node(
        node="finalize",
        action=subgraph_finalize_node,
    )

    # 设置子图边
    subgraph.add_edge(start_key=START, end_key="process")
    subgraph.add_edge(start_key="process", end_key="validate")
    subgraph.add_edge(start_key="validate", end_key="finalize")

    # 编译子图
    return subgraph.compile()


# 构建父图
def build_parent_graph(subgraph: CompiledStateGraph) -> CompiledStateGraph:
    """构建父图"""
    parent_graph = StateGraph(
        state_schema=ParentGraphRuntimeState,
        input_schema=ParentGraphInput,
        output_schema=ParentGraphOutput,
    )

    # 添加父图节点
    parent_graph.add_node(
        node="init",
        action=parent_init_node,
    )
    parent_graph.add_node(
        node="call_subgraph",
        action=functools.partial(
            parent_call_subgraph_node,
            subgraph=subgraph,
        ),
    )
    parent_graph.add_node(
        node="finalize",
        action=parent_final_node,
    )

    # 设置父图边
    parent_graph.add_edge(start_key=START, end_key="init")
    parent_graph.add_edge(start_key="init", end_key="call_subgraph")
    parent_graph.add_edge(start_key="call_subgraph", end_key="finalize")

    # 编译父图
    return parent_graph.compile()


@pytest.fixture
def subgraph() -> CompiledStateGraph:
    """创建子图"""
    return build_subgraph()


@pytest.fixture
def parent_graph(subgraph: CompiledStateGraph) -> CompiledStateGraph:
    """创建父图"""
    return build_parent_graph(subgraph)


@pytest.mark.asyncio
async def test_subgraph_execution(subgraph: CompiledStateGraph):
    """测试子图独立执行"""

    print("\n=== 开始执行子图 ===")

    # 初始化子图输入
    input_data = SubgraphInput(shared_data=["initial"], private_data="test_data")

    # 执行子图
    result = await subgraph.ainvoke(input=input_data)

    # 验证结果
    print("\nSubgraph execution result:")
    print(f"shared_data: {result['shared_data']}")
    print(f"private_data: {result['private_data']}")

    assert "subgraph_finalized" in result["shared_data"]
    assert result["private_data"] == "finalize_complete"


@pytest.mark.asyncio
async def test_parent_graph_with_subgraph(parent_graph: CompiledStateGraph):
    """测试父图调用子图"""

    print("\n=== 开始执行父图（包含子图调用）===")

    # 初始化父图输入
    input_data = ParentGraphInput(
        shared_data=["parent_start"], parent_info="workflow_begin"
    )

    # 执行父图
    result = await parent_graph.ainvoke(input=input_data)

    # 验证结果
    print("\nParent graph execution result:")
    print(f"shared_data: {result['shared_data']}")
    print(f"parent_info: {result['parent_info']}")

    assert "parent_completed" in result["shared_data"]
    assert result["parent_info"] == "workflow_complete"


@pytest.mark.asyncio
async def test_subgraph_streaming(parent_graph: CompiledStateGraph):
    """测试子图流式输出"""

    print("\n=== Testing subgraph streaming ===")

    input_data = ParentGraphInput(
        shared_data=["streaming_start"], parent_info="streaming_workflow"
    )

    # 流式执行
    chunks = []
    async for chunk in parent_graph.astream(input=input_data):
        chunks.append(chunk)
        print(f"Stream chunk: {chunk}")

    # 验证流式输出
    assert len(chunks) > 0
    final_chunk = chunks[-1]
    print(f"\nFinal stream result: {final_chunk}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
