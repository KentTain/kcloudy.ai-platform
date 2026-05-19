"""
并行执行工作流单元测试

测试 parallel_execution_demo 模块的所有功能。
"""

import pytest

from demo.examples.langgraph_workflows.parallel_execution_demo import (
    ParallelState,
    SearchResult,
    SearchTask,
    SimpleParallelWorkflow,
    merge_results_node,
    parallel_search_node,
)


class TestSearchTask:
    """测试搜索任务模型"""

    def test_task_initialization(self) -> None:
        """测试任务初始化"""
        task = SearchTask(source="wiki", query="测试")
        assert task.source == "wiki"
        assert task.query == "测试"

    def test_task_empty(self) -> None:
        """测试空任务"""
        task = SearchTask()
        assert task.source == ""
        assert task.query == ""


class TestSearchResult:
    """测试搜索结果模型"""

    def test_result_initialization(self) -> None:
        """测试结果初始化"""
        result = SearchResult(source="wiki", result="内容", success=True)
        assert result.source == "wiki"
        assert result.result == "内容"
        assert result.success is True

    def test_result_failure(self) -> None:
        """测试失败结果"""
        result = SearchResult(source="wiki", result="", success=False)
        assert result.success is False


class TestParallelState:
    """测试并行状态模型"""

    def test_state_initialization(self) -> None:
        """测试状态初始化"""
        state = ParallelState(query="测试")
        assert state.query == "测试"
        assert state.tasks == []
        assert state.results == []
        assert state.summary == ""

    def test_state_with_tasks(self) -> None:
        """测试带任务的状态"""
        tasks = [SearchTask(source="wiki"), SearchTask(source="news")]
        state = ParallelState(query="测试", tasks=tasks)
        assert len(state.tasks) == 2


class TestParallelSearchNode:
    """测试并行检索节点"""

    def test_wiki_search(self) -> None:
        """测试维基百科搜索"""
        task = SearchTask(source="wiki", query="AI")
        result = parallel_search_node(task)
        assert result["source"] == "wiki"
        assert "维基百科" in result["result"]
        assert result["success"] is True

    def test_news_search(self) -> None:
        """测试新闻搜索"""
        task = SearchTask(source="news", query="AI")
        result = parallel_search_node(task)
        assert result["source"] == "news"
        assert "新闻" in result["result"]

    def test_forum_search(self) -> None:
        """测试论坛搜索"""
        task = SearchTask(source="forum", query="AI")
        result = parallel_search_node(task)
        assert result["source"] == "forum"
        assert "论坛" in result["result"]

    def test_doc_search(self) -> None:
        """测试文档搜索"""
        task = SearchTask(source="doc", query="AI")
        result = parallel_search_node(task)
        assert result["source"] == "doc"
        assert "文档" in result["result"]

    def test_unknown_source(self) -> None:
        """测试未知数据源"""
        task = SearchTask(source="unknown", query="AI")
        result = parallel_search_node(task)
        assert "未知" in result["result"]


class TestMergeResultsNode:
    """测试结果汇总节点"""

    def test_merge_success_results(self) -> None:
        """测试汇总成功结果"""
        results = [
            {"source": "wiki", "result": "内容1", "success": True},
            {"source": "news", "result": "内容2", "success": True},
        ]
        state = ParallelState(query="测试", results=results)
        result = merge_results_node(state)

        assert "汇总" in result["summary"]
        assert "2/2" in result["summary"]

    def test_merge_partial_results(self) -> None:
        """测试汇总部分失败结果"""
        results = [
            {"source": "wiki", "result": "内容1", "success": True},
            {"source": "news", "result": "", "success": False},
        ]
        state = ParallelState(query="测试", results=results)
        result = merge_results_node(state)

        assert "1/2" in result["summary"]

    def test_merge_empty_results(self) -> None:
        """测试汇总空结果"""
        state = ParallelState(query="测试", results=[])
        result = merge_results_node(state)

        assert "0/0" in result["summary"]


class TestSimpleParallelWorkflow:
    """测试简化版并行工作流"""

    @pytest.fixture
    def workflow(self) -> SimpleParallelWorkflow:
        """创建工作流实例"""
        return SimpleParallelWorkflow()

    def test_workflow_creation(self, workflow: SimpleParallelWorkflow) -> None:
        """测试工作流创建"""
        assert workflow.app is not None

    def test_workflow_execution(self, workflow: SimpleParallelWorkflow) -> None:
        """测试工作流执行"""
        result = workflow.run("人工智能")
        # 检查结果存在
        assert "results" in result
        assert len(result["results"]) == 3

    def test_multiple_queries(self, workflow: SimpleParallelWorkflow) -> None:
        """测试多次查询"""
        result1 = workflow.run("Python")
        result2 = workflow.run("JavaScript")

        assert result1["query"] == "Python"
        assert result2["query"] == "JavaScript"

    def test_result_sources(self, workflow: SimpleParallelWorkflow) -> None:
        """测试结果来源"""
        result = workflow.run("测试")
        sources = {r["source"] for r in result["results"]}
        assert "wiki" in sources
        assert "news" in sources
        assert "forum" in sources


class TestEdgeCases:
    """边界条件测试"""

    @pytest.fixture
    def workflow(self) -> SimpleParallelWorkflow:
        """创建工作流实例"""
        return SimpleParallelWorkflow()

    def test_empty_query(self, workflow: SimpleParallelWorkflow) -> None:
        """测试空查询"""
        result = workflow.run("")
        assert "results" in result
        assert len(result["results"]) == 3

    def test_long_query(self, workflow: SimpleParallelWorkflow) -> None:
        """测试超长查询"""
        long_query = "测试" * 1000
        result = workflow.run(long_query)
        assert result["query"] == long_query

    def test_special_characters(self, workflow: SimpleParallelWorkflow) -> None:
        """测试特殊字符"""
        result = workflow.run("@#$%^&*()")
        assert "results" in result

    def test_unicode_query(self, workflow: SimpleParallelWorkflow) -> None:
        """测试 Unicode 查询"""
        result = workflow.run("测试🎉🚀")
        assert "results" in result
