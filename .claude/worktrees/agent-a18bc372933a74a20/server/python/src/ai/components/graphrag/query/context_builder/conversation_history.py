"""用于存储和管理对话历史的类。

Classes for storing and managing conversation history.
"""

from dataclasses import dataclass
from enum import Enum

import pandas as pd
import tiktoken

from ai.components.graphrag.query.llm.text_utils import num_tokens


class ConversationRole(str, Enum):
    """
    对话角色枚举。

    Enum for conversation roles.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    @staticmethod
    def from_string(value: str) -> "ConversationRole":
        """
        将字符串转换为 ConversationRole。

        Convert string to ConversationRole.

        参数 Parameters
        ----------
        - value (str): 角色字符串。Role string

        返回 Returns
        -------
        - ConversationRole: 对话角色枚举值。ConversationRole enum value

        异常 Raises
        ------
        - ValueError: 如果角色值无效。If role value is invalid
        """
        if value == "system":
            return ConversationRole.SYSTEM
        if value == "user":
            return ConversationRole.USER
        if value == "assistant":
            return ConversationRole.ASSISTANT

        msg = f"Invalid Role: {value}"
        raise ValueError(msg)

    def __str__(self) -> str:
        """
        返回枚举值的字符串表示。

        Return string representation of the enum value.
        """
        return self.value


@dataclass
class ConversationTurn:
    """
    用于存储单个对话轮次的数据类。

    Data class for storing a single conversation turn.
    """

    role: ConversationRole
    content: str

    def __str__(self) -> str:
        """
        返回对话轮次的字符串表示。

        Return string representation of the conversation turn.
        """
        return f"{self.role}: {self.content}"


@dataclass
class QATurn:
    """
    用于存储问答轮次的数据类。

    问答轮次包含一个用户问题和一个或多个助手回答。

    Data class for storing a QA turn.

    A QA turn contains a user question and one more multiple assistant answers.
    """

    user_query: ConversationTurn
    assistant_answers: list[ConversationTurn] | None = None

    def get_answer_text(self) -> str | None:
        """
        获取助手回答的文本。

        Get the text of the assistant answers.

        返回 Returns
        -------
        - str | None: 助手回答文本。Assistant answers text
        """
        return (
            "\n".join([answer.content for answer in self.assistant_answers])
            if self.assistant_answers
            else None
        )

    def __str__(self) -> str:
        """
        返回问答轮次的字符串表示。

        Return string representation of the QA turn.
        """
        answers = self.get_answer_text()
        return (
            f"Question: {self.user_query.content}\nAnswer: {answers}"
            if answers
            else f"Question: {self.user_query.content}"
        )


class ConversationHistory:
    """
    用于存储对话历史的类。

    Class for storing a conversation history.
    """

    turns: list[ConversationTurn]

    def __init__(self):
        """
        初始化对话历史。

        Initialize conversation history.
        """
        self.turns = []

    @classmethod
    def from_list(
        cls, conversation_turns: list[dict[str, str]]
    ) -> "ConversationHistory":
        """
        从对话轮次列表创建对话历史。

        每个轮次都是一个字典,格式为 {"role": "<conversation_role>", "content": "<turn content>"}

        Create a conversation history from a list of conversation turns.

        Each turn is a dictionary in the form of {"role": "<conversation_role>", "content": "<turn content>"}

        参数 Parameters
        ----------
        - conversation_turns (list[dict[str, str]]): 对话轮次列表。List of conversation turns

        返回 Returns
        -------
        - ConversationHistory: 对话历史对象。ConversationHistory object
        """
        history = cls()
        for turn in conversation_turns:
            history.turns.append(
                ConversationTurn(
                    role=ConversationRole.from_string(
                        turn.get("role", ConversationRole.USER)
                    ),
                    content=turn.get("content", ""),
                )
            )
        return history

    def add_turn(self, role: ConversationRole, content: str):
        """
        向对话历史添加新的轮次。

        Add a new turn to the conversation history.

        参数 Parameters
        ----------
        - role (ConversationRole): 对话角色。Conversation role
        - content (str): 对话内容。Conversation content
        """
        self.turns.append(ConversationTurn(role=role, content=content))

    def to_qa_turns(self) -> list[QATurn]:
        """
        将对话历史转换为问答轮次列表。

        Convert conversation history to a list of QA turns.

        返回 Returns
        -------
        - list[QATurn]: 问答轮次列表。List of QA turns
        """
        qa_turns = list[QATurn]()
        current_qa_turn = None
        # 遍历对话轮次,将其组织为问答对
        # Iterate through conversation turns and organize into QA pairs
        for turn in self.turns:
            if turn.role == ConversationRole.USER:
                if current_qa_turn:
                    qa_turns.append(current_qa_turn)
                current_qa_turn = QATurn(user_query=turn, assistant_answers=[])
            else:
                if current_qa_turn:
                    current_qa_turn.assistant_answers.append(turn)  # type: ignore
        if current_qa_turn:
            qa_turns.append(current_qa_turn)
        return qa_turns

    def get_user_turns(self, max_user_turns: int | None = 1) -> list[str]:
        """
        获取对话历史中最后的用户轮次。

        Get the last user turns in the conversation history.

        参数 Parameters
        ----------
        - max_user_turns (int | None): 最大用户轮次数。Maximum number of user turns

        返回 Returns
        -------
        - list[str]: 用户轮次内容列表。List of user turn contents
        """
        user_turns = []
        for turn in self.turns[::-1]:
            if turn.role == ConversationRole.USER:
                user_turns.append(turn.content)
                if max_user_turns and len(user_turns) >= max_user_turns:
                    break
        return user_turns

    def build_context(
        self,
        token_encoder: tiktoken.Encoding | None = None,
        include_user_turns_only: bool = True,
        max_qa_turns: int | None = 5,
        max_tokens: int = 8000,
        recency_bias: bool = True,
        column_delimiter: str = "|",
        context_name: str = "Conversation History",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """
        将对话历史准备为系统提示词的上下文数据。

        Prepare conversation history as context data for system prompt.

        参数 Parameters
        ----------
        - token_encoder (tiktoken.Encoding | None): 令牌编码器。Token encoder
        - include_user_turns_only (bool): 如果为 True,则仅包含用户查询(不包含助手响应),默认为 True。If True, only user queries (not assistant responses) will be included in the context, default is True
        - max_qa_turns (int | None): 上下文中包含的最大问答轮次数,默认为 1。Maximum number of QA turns to include in the context, default is 1
        - max_tokens (int): 最大令牌数。Maximum tokens
        - recency_bias (bool): 如果为 True,则反转对话历史顺序以确保最后的问答优先。If True, reverse the order of the conversation history to ensure last QA got prioritized
        - column_delimiter (str): 上下文数据中用于分隔列的分隔符,默认为 "|"。Delimiter to use for separating columns in the context data, default is "|"
        - context_name (str): 上下文名称,默认为 "Conversation History"。Name of the context, default is "Conversation History"

        返回 Returns
        -------
        - tuple[str, dict[str, pd.DataFrame]]: 上下文文本和数据表字典。Context text and data tables dictionary
        """
        # 将对话历史转换为问答轮次
        # Convert conversation history to QA turns
        qa_turns = self.to_qa_turns()
        # 如果仅包含用户轮次,则移除助手回答
        # If only user turns, remove assistant answers
        if include_user_turns_only:
            qa_turns = [
                QATurn(user_query=qa_turn.user_query, assistant_answers=None)
                for qa_turn in qa_turns
            ]
        # 如果需要最近偏差,则反转顺序
        # If recency bias, reverse order
        if recency_bias:
            qa_turns = qa_turns[::-1]
        # 限制问答轮次数量
        # Limit number of QA turns
        if max_qa_turns and len(qa_turns) > max_qa_turns:
            qa_turns = qa_turns[:max_qa_turns]

        # 构建问答轮次的上下文
        # build context for qa turns
        # 添加上下文标题
        # add context header
        if len(qa_turns) == 0 or not qa_turns:
            return ("", {context_name: pd.DataFrame()})

        # 添加表头
        # add table header
        header = f"-----{context_name}-----" + "\n"

        turn_list = []
        current_context_df = pd.DataFrame()
        # 遍历问答轮次并构建上下文
        # Iterate through QA turns and build context
        for turn in qa_turns:
            turn_list.append(
                {
                    "turn": ConversationRole.USER.__str__(),
                    "content": turn.user_query.content,
                }
            )
            if turn.assistant_answers:
                turn_list.append(
                    {
                        "turn": ConversationRole.ASSISTANT.__str__(),
                        "content": turn.get_answer_text(),
                    }
                )

            context_df = pd.DataFrame(turn_list)
            context_text = header + context_df.to_csv(sep=column_delimiter, index=False)
            # 检查是否超过令牌限制
            # Check if token limit is exceeded
            if num_tokens(context_text, token_encoder) > max_tokens:
                break

            current_context_df = context_df
        context_text = header + current_context_df.to_csv(
            sep=column_delimiter, index=False
        )
        return (context_text, {context_name.lower(): current_context_df})
