"""
并行执行节点示例

演示如何使用 LangGraph 的 Send API 实现并行执行。
包括：并行节点定义、Send API 使用、结果汇总。

Day 5 讲义：AI 智能体应用实战 - 工作流深化设计
"""

from typing import Annotated, Any

from langgraph.graph import END, StateGraph
from langgraph.types import Send
from pydantic import BaseModel

# ==================== 状态定义 ====================


class SearchTask(BaseModel):
    """单个搜索任务"""

    source: str = ""
    query: str = ""


class SearchResult(BaseModel):
    """单个搜索结果"""

    source: str = ""
    result: str = ""
    success: bool = True


class ParallelState(BaseModel):
    """
    并行执行状态

    支持多任务并行执行和结果收集。
    """

    # 原始查询
    query: str = ""

    # 并行任务列表
    tasks: list[SearchTask] = []

    # 并行结果列表
    results: Annotated[list[dict[str, Any]], "结果列表"] = []

    # 最终汇总结果
    summary: str = ""

    # 消息历史
    messages: Annotated[list[str], "消息列表"] = []


# ==================== 并行检索节点 ====================


def parallel_search_node(state: SearchTask) -> dict[str, Any]:
    """
    并行检索节点

    每个节点实例处理一个搜索任务。

    注意：此处为 Mock 实现，生产环境应连接真实数据源。
    """
    # 模拟不同数据源的检索
    mock_responses: dict[str, str] = {
        "wiki": f"维基百科结果：关于 '{state.query}' 的百科解释...",
        "news": f"新闻源结果：关于 '{state.query}' 的最新报道...",
        "forum": f"论坛结果：关于 '{state.query}' 的用户讨论...",
        "doc": f"文档库结果：关于 '{state.query}' 的技术文档...",
    }

    result = mock_responses.get(state.source, f"未知数据源 '{state.source}' 的结果")

    return {
        "source": state.source,
        "result": result,
        "success": True,
    }


# ==================== 结果汇总节点 ====================


def merge_results_node(state: ParallelState) -> dict[str, Any]:
    """
    结果汇总节点

    整合所有并行节点的执行结果。
    """
    # 检查是否有失败的结果
    success_count = sum(1 for r in state.results if r.get("success", False))
    total_count = len(state.results)

    # 构建汇总信息
    summary_parts = [f"查询 '{state.query}' 的检索结果：\n"]

    for result in state.results:
        source = result.get("source", "未知")
        content = result.get("result", "")
        summary_parts.append(f"- [{source}] {content}\n")

    summary_parts.append(f"\n汇总：成功 {success_count}/{total_count} 个数据源")

    summary = "".join(summary_parts)

    return {
        "summary": summary,
        "messages": [f"[汇总] 完成 {success_count}/{total_count} 个并行任务"],
    }


# ==================== 分发函数 ====================


def distribute_tasks(state: ParallelState) -> list[Send]:
    """
    任务分发函数

    使用 Send API 创建并行分支。

    Returns:
        Send 对象列表，每个对象触发一个并行节点实例
    """
    # 为每个任务创建一个 Send
    sends = []
    for task in state.tasks:
        sends.append(
            Send(
                "parallel_search",  # 目标节点名称
                SearchTask(
                    source=task.source,
                    query=state.query,
                ),
            )
        )
    return sends


# ==================== 工作流构建 ====================


class ParallelExecutionWorkflow:
    """并行执行工作流"""

    def __init__(self) -> None:
        """初始化工作流"""
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(ParallelState)

        # 添加节点
        # 注意：parallel_search 是一个特殊的节点，用于接收 Send 的输入
        workflow.add_node("parallel_search", self._collect_parallel_result)
        workflow.add_node("merge_results", merge_results_node)

        # 设置入口点 -> 通过条件边分发任务
        # 由于 LangGraph 的限制，我们需要一个入口节点
        workflow.add_node("prepare_tasks", self._prepare_tasks_node)
        workflow.set_entry_point("prepare_tasks")

        # 从 prepare_tasks 通过 Send 并行分发
        workflow.add_conditional_edges("prepare_tasks", distribute_tasks)

        # 所有并行结果汇总到 merge_results
        workflow.add_edge("parallel_search", "merge_results")
        workflow.add_edge("merge_results", END)

        return workflow.compile()

    def _prepare_tasks_node(self, state: ParallelState) -> dict[str, Any]:
        """准备任务节点"""
        # 如果没有任务，创建默认任务
        if not state.tasks:
            state.tasks = [
                SearchTask(source="wiki"),
                SearchTask(source="news"),
                SearchTask(source="forum"),
            ]

        return {
            "messages": [f"[准备] 创建 {len(state.tasks)} 个并行任务"],
        }

    def _collect_parallel_result(self, state: SearchTask) -> dict[str, Any]:
        """收集并行结果"""
        result = parallel_search_node(state)
        # 返回需要追加到 results 列表的结果
        return {"results": [result]}

    def run(
        self,
        query: str,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        执行工作流

        Args:
            query: 用户查询
            sources: 数据源列表（可选）

        Returns:
            最终状态
        """
        tasks = []
        if sources:
            tasks = [SearchTask(source=s) for s in sources]

        initial_state = ParallelState(query=query, tasks=tasks)
        return self.app.invoke(initial_state)


# ==================== 简化版并行工作流 ====================


class SimpleParallelWorkflow:
    """
    简化版并行工作流

    使用顺序执行模拟并行概念，适合理解工作流的基本结构。
    实际生产环境应使用 Send API 实现真正的并行执行。
    """

    def __init__(self) -> None:
        """初始化工作流"""
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(ParallelState)

        # 添加节点
        workflow.add_node("collect_all", self._collect_all_sources)
        workflow.add_node("merge_results", merge_results_node)

        # 设置入口点
        workflow.set_entry_point("collect_all")

        # 顺序执行：收集所有结果 -> 汇总
        workflow.add_edge("collect_all", "merge_results")
        workflow.add_edge("merge_results", END)

        return workflow.compile()

    def _collect_all_sources(self, state: ParallelState) -> dict[str, Any]:
        """收集所有数据源结果（模拟并行）"""
        results = [
            {
                "source": "wiki",
                "result": f"维基百科：关于 '{state.query}' 的解释...",
                "success": True,
            },
            {
                "source": "news",
                "result": f"新闻：关于 '{state.query}' 的报道...",
                "success": True,
            },
            {
                "source": "forum",
                "result": f"论坛：关于 '{state.query}' 的讨论...",
                "success": True,
            },
        ]
        return {
            "results": results,
            "messages": [f"[收集] 已收集 {len(results)} 个数据源结果"],
        }

    def run(self, query: str) -> dict[str, Any]:
        """执行工作流"""
        initial_state = ParallelState(query=query)
        return self.app.invoke(initial_state)


# ==================== 演示函数 ====================


def demo_parallel_execution() -> None:
    """演示并行执行工作流"""
    print("=== 并行执行工作流示例 ===\n")

    workflow = SimpleParallelWorkflow()

    result = workflow.run("人工智能发展趋势")

    print("查询：人工智能发展趋势")
    print("-" * 40)
    print(f"结果数：{len(result['results'])}")
    print(f"\n汇总结果：\n{result['summary']}")


def demo_custom_sources() -> None:
    """演示自定义数据源"""
    print("\n=== 自定义数据源示例 ===\n")

    workflow = SimpleParallelWorkflow()

    result = workflow.run("Python 编程技巧")

    print("查询：Python 编程技巧")
    print("-" * 40)

    for r in result["results"]:
        print(f"- [{r['source']}] {r['result']}")


if __name__ == "__main__":
    demo_parallel_execution()
    demo_custom_sources()
