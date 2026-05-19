"""LangGraph 重试机制示例

演示如何为节点配置 RetryPolicy 实现自动重试。

## 核心概念

### 1. 重试策略
- **RetryPolicy**：定义节点的重试行为
- **max_attempts**：最大尝试次数（包括第一次）
- **backoff_factor**：重试间隔的退避因子
- **retry_on**：自定义重试条件函数

### 2. 工作流程

START -> node (with retry) -> END

### 3. 关键特性

#### 自定义重试条件
- 只有特定类型的错误才会触发重试
- 其他错误直接抛出

#### 退避策略
- 重试间隔按 backoff_factor 指数增长
- 最大间隔不超过 max_interval
"""

from typing import TypedDict

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.types import RetryPolicy


# 定义图状态
class State(TypedDict):
    counter: int
    result: str


# 全局计数器，用于跟踪节点执行次数
execution_count = 0


# 模拟会失败的节点
def node_run(state: State) -> State:
    """模拟会失败的节点，前2次失败，第3次成功"""
    global execution_count
    execution_count += 1

    # 前2次执行失败，第3次成功
    if execution_count < 3:
        print(f"[Error] 第 {execution_count} 次执行失败")
        raise RuntimeError(f"模拟失败 - 第 {execution_count} 次尝试")

    print(f"[Success] 第 {execution_count} 次执行成功")
    return {
        "counter": state.get("counter", 0) + 1,
        "result": f"成功执行，总计尝试 {execution_count} 次",
    }


@pytest.mark.asyncio
async def test_langgraph_retry():
    """测试 LangGraph 的重试机制"""
    global execution_count

    # 重置全局状态
    execution_count = 0

    print("[Test] 开始测试 LangGraph 重试机制")

    # 定义重试策略
    def should_retry(error: Exception) -> bool:
        """决定是否重试的函数"""
        print(f"[Retry Check] 检查错误: {type(error).__name__}: {str(error)}")
        return isinstance(error, RuntimeError)

    # 定义重试策略
    retry_policy = RetryPolicy(
        max_attempts=3,  # 最多尝试3次（包括第一次）
        backoff_factor=0.1,  # 退避因子，重试间隔
        max_interval=1.0,  # 最大重试间隔
        retry_on=should_retry,
    )

    # 构建图
    builder = StateGraph(State)

    # 添加节点，并为 node 设置重试策略
    builder.add_node("node", node_run, retry_policy=retry_policy)

    # 设置边
    builder.set_entry_point("node")
    builder.add_edge("node", END)

    # 编译图
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    # 执行图
    result = await graph.ainvoke(
        {
            "counter": 0,
            "result": "",
        },
        config={
            "configurable": {
                "thread_id": "test_retry",
            },
        },
    )

    print("执行统计:")
    print(f"   节点执行次数: {execution_count}")
    print(f"   最终状态: {result}")

    # 验证重试机制是否正常工作
    assert execution_count == 3, f"期望执行3次，实际执行{execution_count}次"
    assert result["result"] == "成功执行，总计尝试 3 次"
    assert result["counter"] == 1

    print("[PASS] 重试机制测试通过！")


@pytest.mark.asyncio
async def test_retry_policy_max_attempts():
    """测试重试策略的 max_attempts 限制"""
    global execution_count
    execution_count = 0

    # 定义一个总是会失败的策略（只允许2次尝试）
    retry_policy = RetryPolicy(
        max_attempts=2,
        retry_on=lambda e: True,  # 所有错误都重试
    )

    def always_fail(state: State) -> State:
        global execution_count
        execution_count += 1
        raise RuntimeError(f"总是失败 - 第 {execution_count} 次")

    builder = StateGraph(State)
    builder.add_node("node", always_fail, retry_policy=retry_policy)
    builder.set_entry_point("node")
    builder.add_edge("node", END)

    graph = builder.compile(checkpointer=InMemorySaver())

    # 应该抛出异常
    with pytest.raises(RuntimeError):
        await graph.ainvoke(
            {"counter": 0, "result": ""},
            config={"configurable": {"thread_id": "test_max_attempts"}},
        )

    # 验证只执行了2次
    assert execution_count == 2, f"期望执行2次，实际执行{execution_count}次"
    print("[PASS] max_attempts 限制测试通过！")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
