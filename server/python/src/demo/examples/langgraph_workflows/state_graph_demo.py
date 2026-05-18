"""
StateGraph 状态图基础示例

演示如何使用 LangGraph 的 StateGraph 创建状态工作流。
包括状态定义、节点创建、边连接和图执行。

Day 3 讲义：AI 智能体应用实战 - LangGraph 工作流
"""

from typing import Annotated, Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel


# ==================== 状态定义 ====================


class WorkflowState(BaseModel):
    """
    工作流状态

    使用 Pydantic 模型定义状态结构，确保类型安全。
    """

    # 输入数据
    query: str = ""

    # 处理阶段
    current_step: str = "start"

    # 处理结果
    analysis: str = ""
    plan: str = ""
    result: str = ""

    # 计数器
    step_count: int = 0

    # 消息历史
    messages: Annotated[list[str], "追加消息"] = []


# ==================== 节点函数 ====================


def analyze_node(state: WorkflowState) -> dict[str, Any]:
    """
    分析节点

    分析用户查询，提取关键信息。

    Args:
        state: 当前状态

    Returns:
        状态更新
    """
    # 模拟分析过程
    analysis = f"分析查询 '{state.query}'：识别为数据处理任务"

    return {
        "current_step": "analyze",
        "analysis": analysis,
        "step_count": state.step_count + 1,
        "messages": [f"[分析] {analysis}"],
    }


def plan_node(state: WorkflowState) -> dict[str, Any]:
    """
    规划节点

    根据分析结果制定执行计划。

    Args:
        state: 当前状态

    Returns:
        状态更新
    """
    # 模拟规划过程
    plan = f"执行计划：\n1. 数据验证\n2. 数据处理\n3. 结果输出"

    return {
        "current_step": "plan",
        "plan": plan,
        "step_count": state.step_count + 1,
        "messages": [f"[规划] {plan}"],
    }


def execute_node(state: WorkflowState) -> dict[str, Any]:
    """
    执行节点

    执行处理计划，生成最终结果。

    Args:
        state: 当前状态

    Returns:
        状态更新
    """
    # 模拟执行过程
    result = f"执行完成：已处理查询 '{state.query}'"

    return {
        "current_step": "execute",
        "result": result,
        "step_count": state.step_count + 1,
        "messages": [f"[执行] {result}"],
    }


def summarize_node(state: WorkflowState) -> dict[str, Any]:
    """
    总结节点

    汇总处理过程和结果。

    Args:
        state: 当前状态

    Returns:
        状态更新
    """
    summary = f"""
=== 处理总结 ===
查询：{state.query}
步骤数：{state.step_count}
分析结果：{state.analysis}
执行结果：{state.result}
"""

    return {
        "current_step": "summarize",
        "messages": [f"[总结] 处理完成"],
    }


# ==================== 图构建 ====================


def create_simple_workflow() -> StateGraph:
    """
    创建简单的工作流图

    定义节点和边，构建状态图。

    Returns:
        编译后的状态图
    """
    # 创建状态图
    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("summarize", summarize_node)

    # 设置入口点
    workflow.set_entry_point("analyze")

    # 添加边（定义执行顺序）
    workflow.add_edge("analyze", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "summarize")
    workflow.add_edge("summarize", END)

    # 编译图
    return workflow.compile()


# ==================== 演示函数 ====================


def demo_state_graph() -> None:
    """演示状态图"""
    print("=== StateGraph 基础示例 ===\n")

    # 创建工作流
    app = create_simple_workflow()

    # 初始化状态
    initial_state = WorkflowState(query="帮我分析销售数据")

    print(f"初始状态：{initial_state.model_dump()}\n")
    print("-" * 50)

    # 执行工作流
    print("\n开始执行工作流...\n")

    final_state = app.invoke(initial_state)

    print("-" * 50)
    print(f"\n最终状态：")
    print(f"  当前步骤: {final_state['current_step']}")
    print(f"  步骤数: {final_state['step_count']}")
    print(f"  结果: {final_state['result']}")

    print(f"\n消息历史：")
    for msg in final_state["messages"]:
        print(f"  {msg}")


def demo_state_mutation() -> None:
    """演示状态变更"""
    print("\n=== 状态变更示例 ===\n")

    # 创建工作流
    app = create_simple_workflow()

    # 使用流式执行观察中间状态
    initial_state = WorkflowState(query="分析用户行为数据")

    print("流式执行工作流：\n")

    for event in app.stream(initial_state):
        for node_name, node_output in event.items():
            print(f"节点 '{node_name}' 输出：")
            print(f"  step_count: {node_output.get('step_count', 'N/A')}")
            print(f"  current_step: {node_output.get('current_step', 'N/A')}")
            if node_output.get("messages"):
                print(f"  最新消息: {node_output['messages'][-1]}")
            print()


if __name__ == "__main__":
    demo_state_graph()
    demo_state_mutation()
