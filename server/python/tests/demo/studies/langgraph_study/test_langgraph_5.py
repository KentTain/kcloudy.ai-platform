"""LangGraph 暂停恢复功能测试

演示 LangGraph 的中断（interrupt）和恢复（resume）机制。

核心概念：
- interrupt(): 在节点中调用，暂停图执行
- Command(resume=value): 恢复执行并传递数据
- InMemorySaver: 状态持久化检查点
- thread_id: 区分不同执行会话

工作流：
START → node1 → decision_node → node2 → node3 → END
                      ↓ (random=false)
                 interrupt(暂停)
"""

import logging
import random
import uuid
from dataclasses import dataclass
from operator import add
from typing import Annotated

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt

_logger = logging.getLogger(__name__)


@dataclass
class GraphState:
    """图运行状态"""

    result: Annotated[list[str], add]
    decision_made: bool = False
    pause_point: str = ""
    step_count: int = 0


def node1_func(state: GraphState) -> GraphState:
    """节点1处理函数"""
    print(f"\n[Node 1] result: {state.result}, step: {state.step_count}")
    return GraphState(
        result=["node1"],
        decision_made=state.decision_made,
        pause_point=state.pause_point,
        step_count=state.step_count + 1,
    )


def decision_node_func(state: GraphState) -> GraphState:
    """决策节点：执行随机判断，可能暂停执行

    这是 LangGraph 的核心特性演示：
    - interrupt() 调用会暂停图执行
    - 暂停后状态被保存到 checkpointer
    - 可以使用 Command(resume=value) 恢复执行
    """
    print(f"\n[Decision Node] result: {state.result}, step: {state.step_count}")

    new_step_count = state.step_count + 1

    # 生成随机决策
    random_decision = random.choice([True, False])
    print(f"Random decision: {random_decision}")

    if random_decision:
        # 继续执行
        print("Decision is True, continuing execution...")
        return GraphState(
            result=["decision_continue"], decision_made=True, step_count=new_step_count
        )
    else:
        # 暂停执行
        print("Decision is False, pausing execution...")
        pause_point_id = f"pause_{uuid.uuid4().hex[:8]}"

        # 调用 interrupt 暂停执行
        # interrupt() 会返回恢复时传入的值
        resume_value = interrupt(
            {
                "message": "Execution paused due to random decision",
                "pause_point_id": pause_point_id,
                "current_state": state.result,
                "step_count": new_step_count,
            }
        )

        print(f"Resumed with value: {resume_value}")

        # 根据恢复值决定后续行为
        if resume_value and resume_value.get("action") == "continue":
            print("Resume action is 'continue', proceeding...")
            return GraphState(
                result=["decision_resumed"],
                decision_made=True,
                pause_point=pause_point_id,
                step_count=new_step_count,
            )
        else:
            return GraphState(
                result=["decision_default"],
                decision_made=True,
                pause_point=pause_point_id,
                step_count=new_step_count,
            )


def node2_func(state: GraphState) -> GraphState:
    """节点2处理函数"""
    print(f"\n[Node 2] result: {state.result}, step: {state.step_count}")
    return GraphState(
        result=["node2"],
        decision_made=state.decision_made,
        pause_point=state.pause_point,
        step_count=state.step_count + 1,
    )


def node3_func(state: GraphState) -> GraphState:
    """节点3处理函数"""
    print(f"\n[Node 3] result: {state.result}, step: {state.step_count}")
    return GraphState(
        result=["node3"],
        decision_made=state.decision_made,
        pause_point=state.pause_point,
        step_count=state.step_count + 1,
    )


def build_graph() -> CompiledStateGraph:
    """构建带有暂停恢复功能的状态图

    关键点：
    1. 使用 InMemorySaver 作为 checkpointer
    2. 没有checkpointer，interrupt() 功能无法工作
    """
    graph = StateGraph(state_schema=GraphState)

    # 添加节点
    graph.add_node(node="node1", action=node1_func)
    graph.add_node(node="decision_node", action=decision_node_func)
    graph.add_node(node="node2", action=node2_func)
    graph.add_node(node="node3", action=node3_func)

    # 设置边
    graph.add_edge(start_key="node1", end_key="decision_node")
    graph.add_edge(start_key="decision_node", end_key="node2")
    graph.add_edge(start_key="node2", end_key="node3")

    # 设置入口和结束点
    graph.set_entry_point(key="node1")
    graph.set_finish_point(key="node3")

    # 编译图（必须传入 checkpointer 才能使用 interrupt 功能）
    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)


@pytest.fixture
def graph() -> CompiledStateGraph:
    """创建图 fixture"""
    return build_graph()


@pytest.mark.asyncio
async def test_graph_run_without_interrupt(graph: CompiledStateGraph):
    """测试图正常执行（可能触发中断）"""
    print("\n" + "=" * 60)
    print("测试 LangGraph 执行（可能触发中断）")
    print("=" * 60)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "result": [],
        "decision_made": False,
        "pause_point": "",
        "step_count": 0,
    }

    result = await graph.ainvoke(initial_state, config=config)

    print(f"\n最终结果: {result['result']}")
    print(f"决策完成: {result['decision_made']}")
    print(f"步骤计数: {result['step_count']}")

    # 检查是否发生了中断
    if "__interrupt__" in result:
        print(f"\n检测到中断: {result['__interrupt__']}")


@pytest.mark.asyncio
async def test_graph_pause_and_resume(graph: CompiledStateGraph):
    """测试图的暂停和恢复功能"""
    print("\n" + "=" * 60)
    print("测试 LangGraph 暂停恢复功能")
    print("=" * 60)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "result": [],
        "decision_made": False,
        "pause_point": "",
        "step_count": 0,
    }

    # 第一次执行
    print("\n第一次执行图...")
    result = await graph.ainvoke(initial_state, config=config)

    # 检查是否发生了中断
    if "__interrupt__" in result:
        print("\n检测到中断！")
        interrupts = result["__interrupt__"]
        print(f"中断信息: {interrupts}")

        # 获取状态快照
        state_snapshot = graph.get_state(config)
        print(f"\n状态快照: {state_snapshot.values}")
        print(f"下一个节点: {state_snapshot.next}")

        # 恢复执行
        print("\n开始恢复执行...")
        resume_command = Command(
            resume={"action": "continue", "message": "User decided to continue"}
        )

        # 使用同一个 config（相同 thread_id）恢复执行
        final_result = await graph.ainvoke(resume_command, config=config)

        print("\n恢复执行完成")
        print(f"最终结果: {final_result['result']}")
        print(f"决策完成: {final_result['decision_made']}")

        # 验证恢复后的执行是否完整
        assert final_result["decision_made"] is True
        assert (
            "decision_resumed" in final_result["result"]
            or "decision_default" in final_result["result"]
        )

    else:
        print("\n图正常完成，未发生中断")
        print(f"结果: {result['result']}")


@pytest.mark.asyncio
async def test_multiple_pause_resume_cycles():
    """测试多次暂停恢复循环

    演示如何处理多次可能的中断情况。
    """
    print("\n" + "=" * 60)
    print("测试多次暂停恢复循环")
    print("=" * 60)

    max_attempts = 5
    successful_resumes = 0

    for attempt in range(max_attempts):
        print(f"\n--- 第 {attempt + 1} 次尝试 ---")

        graph = build_graph()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "result": [],
            "decision_made": False,
            "pause_point": "",
            "step_count": 0,
        }

        result = await graph.ainvoke(initial_state, config=config)

        if "__interrupt__" in result:
            print(f"尝试 {attempt + 1} 发生中断，尝试恢复...")

            # 恢复执行
            resume_command = Command(resume={"action": "continue"})
            final_result = await graph.ainvoke(resume_command, config=config)

            print(f"尝试 {attempt + 1} 恢复成功")
            print(f"结果: {final_result['result']}")
            successful_resumes += 1

        else:
            print(f"尝试 {attempt + 1} 成功完成，未发生中断")
            print(f"结果: {result['result']}")

    print(f"\n共执行 {max_attempts} 次，成功恢复 {successful_resumes} 次中断")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
