"""
Mock LLM 实现

提供了用于测试的 Mock LLM 实现:
- MockChatLLM: 模拟聊天 LLM,返回预设的响应序列
- MockCompletionLLM: 模拟补全 LLM,返回预设的固定响应
"""

from ai.components.graphrag.llm.mock.mock_chat_llm import MockChatLLM
from ai.components.graphrag.llm.mock.mock_completion_llm import MockCompletionLLM

__all__ = [
    "MockChatLLM",
    "MockCompletionLLM",
]
