"""
记忆与检查点示例

演示如何使用 LangGraph 的检查点机制实现会话持久化。
包括内存检查点和基于线程的会话管理。

Day 3 讲义：AI 智能体应用实战 - LangGraph 工作流
"""

from typing import Annotated, Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

# ==================== 状态定义 ====================


class ConversationState(BaseModel):
    """对话状态"""

    # 当前消息
    current_message: str = ""

    # 对话历史
    history: Annotated[list[dict[str, str]], "对话历史"] = []

    # 用户信息
    user_name: str = ""

    # 会话统计
    message_count: int = 0


# ==================== 节点函数 ====================


def process_message(state: ConversationState) -> dict[str, Any]:
    """
    处理消息节点
    """
    # 记录用户消息
    new_history = state.history.copy()
    new_history.append({"role": "user", "content": state.current_message})

    # 生成模拟回复
    response = f"收到：'{state.current_message}'"

    if state.user_name:
        response = f"{state.user_name}，{response}"

    # 添加助手回复
    new_history.append({"role": "assistant", "content": response})

    return {
        "history": new_history,
        "message_count": state.message_count + 1,
        "current_message": "",  # 清空当前消息
    }


def extract_user_info(state: ConversationState) -> dict[str, Any]:
    """
    提取用户信息节点
    """
    # 模拟从对话中提取用户名
    if not state.user_name and "我是" in state.current_message:
        # 简单的名字提取
        name = state.current_message.split("我是")[-1].strip()
        if len(name) < 10:  # 简单验证
            return {"user_name": name}

    return {}


# ==================== 图构建 ====================


class ConversationGraph:
    """
    对话图

    支持检查点和会话持久化。
    """

    def __init__(self, enable_checkpointer: bool = True) -> None:
        """
        初始化对话图

        Args:
            enable_checkpointer: 是否启用检查点
        """
        self.checkpointer = MemorySaver() if enable_checkpointer else None
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(ConversationState)

        # 添加节点
        workflow.add_node("extract_info", extract_user_info)
        workflow.add_node("process", process_message)

        # 设置入口点
        workflow.set_entry_point("extract_info")

        # 添加边
        workflow.add_edge("extract_info", "process")
        workflow.add_edge("process", END)

        # 编译图
        if self.checkpointer:
            return workflow.compile(checkpointer=self.checkpointer)
        return workflow.compile()

    def chat(
        self,
        message: str,
        thread_id: str = "default",
        initial_state: ConversationState | None = None,
    ) -> dict[str, Any]:
        """
        发送消息

        Args:
            message: 用户消息
            thread_id: 线程ID，用于区分不同会话
            initial_state: 初始状态（仅用于新会话）

        Returns:
            更新后的状态
        """
        # 如果没有检查点，直接执行
        if not self.checkpointer:
            if initial_state is None:
                initial_state = ConversationState()
            initial_state.current_message = message
            return self.app.invoke(initial_state)

        # 配置
        config = {"configurable": {"thread_id": thread_id}}

        # 获取当前状态（如果存在）
        current_state = self.app.get_state(config)

        if current_state.values:
            # 已有状态，更新当前消息
            state_update = {"current_message": message}
            result = self.app.invoke(state_update, config)
        else:
            # 新状态
            if initial_state is None:
                initial_state = ConversationState()
            initial_state.current_message = message
            result = self.app.invoke(initial_state, config)

        return result

    def get_history(self, thread_id: str = "default") -> list[dict[str, str]]:
        """
        获取对话历史

        Args:
            thread_id: 线程ID

        Returns:
            对话历史列表
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)

        if state.values:
            return state.values.get("history", [])
        return []

    def get_state(self, thread_id: str = "default") -> dict[str, Any] | None:
        """
        获取当前状态

        Args:
            thread_id: 线程ID

        Returns:
            当前状态
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)
        return state.values if state.values else None

    def clear_session(self, thread_id: str = "default") -> None:
        """
        清除会话

        Args:
            thread_id: 线程ID
        """
        config = {"configurable": {"thread_id": thread_id}}
        # 通过删除状态来清除会话
        self.app.update_state(config, None)


# ==================== 演示函数 ====================


def demo_memory_checkpoint() -> None:
    """演示记忆与检查点"""
    print("=== 记忆与检查点示例 ===\n")

    # 创建对话图
    graph = ConversationGraph(enable_checkpointer=True)

    # 模拟对话
    thread_id = "session-001"

    print("会话 1 (thread_id: session-001)：")
    print("-" * 40)

    # 第一轮对话
    result1 = graph.chat("你好！", thread_id=thread_id)
    print("用户：你好！")
    print(f"助手：{result1['history'][-1]['content']}")
    print(f"消息数：{result1['message_count']}")

    # 第二轮对话
    result2 = graph.chat("我是小明", thread_id=thread_id)
    print("\n用户：我是小明")
    print(f"助手：{result2['history'][-1]['content']}")
    print(f"用户名：{result2.get('user_name', '未设置')}")
    print(f"消息数：{result2['message_count']}")

    # 第三轮对话 - 验证记忆
    result3 = graph.chat("你还记得我是谁吗？", thread_id=thread_id)
    print("\n用户：你还记得我是谁吗？")
    print(f"助手：{result3['history'][-1]['content']}")
    print(f"用户名：{result3.get('user_name', '未设置')}")
    print(f"消息数：{result3['message_count']}")

    # 查看完整历史
    print("\n完整对话历史：")
    history = graph.get_history(thread_id)
    for i, msg in enumerate(history):
        print(f"  {i + 1}. [{msg['role']}]: {msg['content']}")


def demo_multiple_sessions() -> None:
    """演示多会话管理"""
    print("\n=== 多会话管理示例 ===\n")

    graph = ConversationGraph(enable_checkpointer=True)

    # 会话 A
    print("会话 A：")
    graph.chat("我是张三", thread_id="session-a")
    result_a = graph.chat("我是谁？", thread_id="session-a")
    print(f"  用户名：{result_a.get('user_name', '未设置')}")
    print(f"  消息数：{result_a['message_count']}")

    # 会话 B
    print("\n会话 B：")
    graph.chat("我是李四", thread_id="session-b")
    result_b = graph.chat("我是谁？", thread_id="session-b")
    print(f"  用户名：{result_b.get('user_name', '未设置')}")
    print(f"  消息数：{result_b['message_count']}")

    # 验证会话隔离
    print("\n验证会话隔离：")
    state_a = graph.get_state("session-a")
    state_b = graph.get_state("session-b")
    print(
        f"  会话 A 用户名：{state_a.get('user_name', '未设置') if state_a else '无状态'}"
    )
    print(
        f"  会话 B 用户名：{state_b.get('user_name', '未设置') if state_b else '无状态'}"
    )


def demo_checkpoint_recovery() -> None:
    """演示检查点恢复"""
    print("\n=== 检查点恢复示例 ===\n")

    graph = ConversationGraph(enable_checkpointer=True)
    thread_id = "recovery-test"

    # 建立对话
    graph.chat("第一句话", thread_id=thread_id)
    graph.chat("第二句话", thread_id=thread_id)

    # 获取当前状态
    state_before = graph.get_state(thread_id)
    print(f"对话消息数：{state_before['message_count']}")
    print(f"对话历史长度：{len(state_before['history'])}")

    # 恢复状态（模拟重新加载）
    print("\n恢复会话后：")
    state_after = graph.get_state(thread_id)
    print(f"对话消息数：{state_after['message_count']}")
    print(f"对话历史长度：{len(state_after['history'])}")

    # 继续对话
    result = graph.chat("继续对话", thread_id=thread_id)
    print(f"\n继续对话后消息数：{result['message_count']}")


if __name__ == "__main__":
    demo_memory_checkpoint()
    demo_multiple_sessions()
    demo_checkpoint_recovery()
