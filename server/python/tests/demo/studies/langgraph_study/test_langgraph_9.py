"""LangGraph 单节点多中断示例

演示同一节点内多次调用 interrupt() 的处理方式。

## 核心概念

### 1. 单节点多次中断
- **顺序中断**：节点内有多处 interrupt() 调用时，每次执行只触发第一个未处理的中断
- **状态检查**：通过检查状态判断是否需要继续中断
- **顺序恢复**：使用相同的 thread_id 可以继续恢复

### 2. 工作流程

START -> multi_interrupt_node -> END

在 multi_interrupt_node 内部：
1. 第一次执行：触发第一个中断（获取姓名）
2. 第二次执行：触发第二个中断（获取年龄）
3. 第三次执行：完成处理
"""

import uuid
from typing import TypedDict

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    """图状态"""

    name: str
    age: str
    result: str


def multi_interrupt_node(state: State) -> State:
    """单节点内多次中断的示例"""
    # 第一次中断：获取姓名
    if not state.get("name"):
        name = interrupt({"question": "请输入您的姓名？", "step": 1})
    else:
        name = state["name"]

    # 第二次中断：获取年龄
    if not state.get("age"):
        age = interrupt({"question": "请输入您的年龄？", "step": 2})
    else:
        age = state["age"]

    result = f"用户信息 - 姓名: {name}, 年龄: {age}"
    print(f"[Final] {result}")

    return {"name": name, "age": age, "result": result}


def build_graph() -> StateGraph:
    """构建单节点多中断图"""
    builder = StateGraph(State)
    builder.add_node("multi_interrupt_node", multi_interrupt_node)
    builder.add_edge(START, "multi_interrupt_node")
    builder.add_edge("multi_interrupt_node", END)

    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


@pytest.fixture
def graph():
    """创建图 fixture"""
    return build_graph()


@pytest.mark.asyncio
async def test_single_node_multiple_interrupts(graph):
    """测试单个节点内多次中断的情况"""

    config = {"configurable": {"thread_id": uuid.uuid4()}}

    # 第一次执行 - 触发第一个中断
    result1 = await graph.ainvoke({}, config=config)

    print("\n=== 第一次中断 ===")
    print(f"中断数量: {len(result1['__interrupt__'])}")
    assert len(result1["__interrupt__"]) == 1
    assert result1["__interrupt__"][0].value["step"] == 1

    # 恢复第一个中断
    result2 = await graph.ainvoke(Command(resume="张三"), config=config)

    print("\n=== 第二次中断 ===")
    print(f"中断数量: {len(result2['__interrupt__'])}")
    assert len(result2["__interrupt__"]) == 1
    assert result2["__interrupt__"][0].value["step"] == 2

    # 恢复第二个中断
    final_result = await graph.ainvoke(Command(resume="25"), config=config)

    print("\n=== 最终结果 ===")
    print(final_result)

    assert "name" in final_result
    assert "age" in final_result
    assert final_result["name"] == "张三"
    assert final_result["age"] == "25"

    print("[PASS] 单节点多中断测试通过！")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
