"""LangGraph 并行中断示例

演示如何处理多个并行节点同时触发中断的情况。

## 核心概念

### 1. 并行中断
- **并行节点**：多个节点从同一个 START 边开始并行执行
- **同时中断**：多个并行节点都可以调用 interrupt()
- **中断收集**：所有中断信息会被收集到一个列表中

### 2. 工作流程

START -> [human_review_node_1, human_review_node_2] (并行) -> combine_summaries -> END

### 3. 恢复机制

- 使用 `Command(resume=resume_map)` 恢复
- `resume_map` 需要为每个中断 ID 提供对应的恢复数据
"""

import uuid
from typing import TypedDict

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt


# 定义图状态
class State(TypedDict):
    summary_1: str
    summary_2: str
    final_result: str


# 并行节点1：生成第一个摘要并请求人工审查
def human_review_node_1(state: State) -> dict:
    """节点1: 生成摘要并请求人工审查"""
    generated_summary = "猫咪坐在垫子上，仰望着满天繁星。"

    feedback = interrupt(
        {
            "task": "请审查并编辑第一个摘要",
            "node_id": "node_1",
            "generated_summary": generated_summary,
        }
    )
    return {
        "summary_1": feedback["edited_summary"],
    }


# 并行节点2：生成第二个摘要并请求人工审查
def human_review_node_2(state: State) -> dict:
    """节点2: 生成摘要并请求人工审查"""
    generated_summary = "小狗在公园里快乐地奔跑。"

    feedback = interrupt(
        {
            "task": "请审查并编辑第二个摘要",
            "node_id": "node_2",
            "generated_summary": generated_summary,
        }
    )
    return {
        "summary_2": feedback["edited_summary"],
    }


# 汇总节点：合并两个审查后的摘要
def combine_summaries(state: State) -> dict:
    """合并两个审查后的摘要"""
    final_result = f"合并结果：{state['summary_1']} | {state['summary_2']}"
    print(f"[Final] {final_result}")
    return {"final_result": final_result}


def build_graph() -> StateGraph:
    """构建并行中断图"""
    builder = StateGraph(State)
    builder.add_node("human_review_node_1", human_review_node_1)
    builder.add_node("human_review_node_2", human_review_node_2)
    builder.add_node("combine_summaries", combine_summaries)

    # 设置并行执行：从START同时进入两个审查节点
    builder.add_edge(START, "human_review_node_1")
    builder.add_edge(START, "human_review_node_2")

    # 两个审查节点都完成后，进入合并节点
    builder.add_edge("human_review_node_1", "combine_summaries")
    builder.add_edge("human_review_node_2", "combine_summaries")

    builder.add_edge("combine_summaries", END)

    # 设置内存检查点以支持中断
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


@pytest.fixture
def graph():
    """创建图 fixture"""
    return build_graph()


@pytest.mark.asyncio
async def test_parallel_interrupts(graph):
    """测试并行节点同时中断"""
    config = {
        "configurable": {
            "thread_id": uuid.uuid4(),
        },
    }

    # 使用astream进行流式处理
    stream_events = []
    values_events = []
    tasks_events = []
    collected_interrupts = []

    print("\n=== 开始流式处理 ===")
    async for event in graph.astream(
        input={},
        config=config,
        stream_mode=[
            "values",  # 默认模式，输出所有节点运行结果
            "tasks",  # 任务输出，可以标记任务开始和结束
            "custom",  # 自定义输出
        ],
    ):
        stream_events.append(event)
        print(f"Stream event: {type(event)} - {event}")

        # 分类收集不同类型的事件
        if isinstance(event, tuple) and len(event) == 2:
            stream_type, data = event
            if stream_type == "values":
                values_events.append(data)
            elif stream_type == "tasks":
                tasks_events.append(data)
                # 在流式模式下，中断信息在tasks事件中
                if (
                    isinstance(data, dict)
                    and "interrupts" in data
                    and data["interrupts"]
                ):
                    for interrupt_data in data["interrupts"]:
                        interrupt_obj = type(
                            "Interrupt",
                            (),
                            {
                                "id": interrupt_data["id"],
                                "value": interrupt_data["value"],
                            },
                        )()
                        collected_interrupts.append(interrupt_obj)
            elif stream_type == "custom":
                pass  # custom events

    print("\n=== 流式事件统计 ===")
    print(f"总事件数: {len(stream_events)}")
    print(f"Values事件数: {len(values_events)}")
    print(f"Tasks事件数: {len(tasks_events)}")

    # 处理中断信息
    interrupts_to_use = collected_interrupts
    if not interrupts_to_use:
        print("\n=== 从流中未获取到中断，尝试从状态获取 ===")
        state = graph.get_state(config)
        if (
            hasattr(state, "values")
            and state.values
            and "__interrupt__" in state.values
        ):
            interrupts_to_use = state.values["__interrupt__"]

    # 输出中断信息
    print("\n=== 并行中断信息 ===")
    print(f"中断数量: {len(interrupts_to_use)}")

    for i, interrupt_obj in enumerate(interrupts_to_use):
        print(f"\n中断 {i + 1}:")
        print(f"  ID: {interrupt_obj.id}")
        print(f"  Node: {interrupt_obj.value['node_id']}")
        print(f"  Task: {interrupt_obj.value['task']}")
        print(f"  Summary: {interrupt_obj.value['generated_summary']}")

    # 验证有两个并行中断
    assert len(interrupts_to_use) == 2, (
        f"期望2个中断，实际得到{len(interrupts_to_use)}个"
    )

    # 准备恢复数据：为每个中断提供编辑后的内容
    resume_map = {}
    for interrupt_obj in interrupts_to_use:
        node_id = interrupt_obj.value["node_id"]
        if node_id == "node_1":
            resume_map[interrupt_obj.id] = {
                "edited_summary": "猫咪优雅地躺在丝绒垫子上，静静凝望夜空中的璀璨星辰。",
            }
        elif node_id == "node_2":
            resume_map[interrupt_obj.id] = {
                "edited_summary": "活泼的小狗在绿草如茵的公园里自由自在地奔跑嬉戏。",
            }

    print("\n=== 恢复映射 ===")
    for interrupt_id, resume_data in resume_map.items():
        print(f"中断ID {interrupt_id}: {resume_data['edited_summary']}")

    # 使用映射同时恢复所有中断
    print("\n=== 恢复执行 ===")
    resume_values_events = []
    resumed_result = None

    async for event in graph.astream(
        input=Command(resume=resume_map),
        config=config,
        stream_mode=["values", "tasks", "custom"],
    ):
        if isinstance(event, tuple) and len(event) == 2:
            stream_type, data = event
            if stream_type == "values":
                resume_values_events.append(data)
                if isinstance(data, dict):
                    resumed_result = data

    # 如果没有通过流获取到最终结果，使用同步方式获取
    if resumed_result is None:
        print("\n=== 获取恢复后的最终状态 ===")
        state = graph.get_state(config)
        resumed_result = state.values if hasattr(state, "values") else state

    print("\n=== 最终结果 ===")
    print(resumed_result)

    # 验证最终结果包含了两个编辑后的摘要
    assert "summary_1" in resumed_result
    assert "summary_2" in resumed_result
    assert "final_result" in resumed_result
    # 验证摘要已被更新（非空）
    assert resumed_result["summary_1"]
    assert resumed_result["summary_2"]
    assert resumed_result["final_result"]

    print("[PASS] 并行中断流式测试通过！")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
