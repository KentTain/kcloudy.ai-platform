"""Skill Chain Builder - 构建基于 LangChain 的 Skill 执行链"""

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class SkillChainBuilder:
    """
    Skill Chain 构建器

    将 Skill 文档转换为 LangChain Runnable Chain
    """

    def __init__(self, llm: Any):
        """
        初始化 Chain 构建器

        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm

    def build_knowledge_skill_chain(
        self, skill_document: str, examples: str = "", context: dict[str, Any] | None = None
    ) -> Any:
        """
        构建知识文档 Chain

        Args:
            skill_document: Skill 文档内容
            examples: 示例文档（可选）
            context: 上下文信息（可选）

        Returns:
            LangChain Runnable Chain
        """
        # 构建 system 消息内容
        system_content = f"""你是一个技能助手，请按照以下技能文档处理用户请求。

# 技能文档
{skill_document}
"""
        if examples:
            system_content += f"""
# 示例
{examples}
"""
        if context:
            system_content += f"""
# 上下文信息
{self._format_context(context)}
"""

        # 创建 prompt 模板
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_content), ("user", "{user_request}")]
        )

        # 构建 chain
        chain = prompt | self.llm | StrOutputParser()

        return chain

    def build_multi_skill_chain(self, skills: list[dict[str, str]], user_request: str) -> Any:
        """
        构建多 Skill 组合 Chain

        Args:
            skills: Skill 列表，每个元素包含 name 和 document
            user_request: 用户请求

        Returns:
            LangChain Runnable Chain
        """
        # 组合所有 Skill 文档
        combined_documents = "\n\n---\n\n".join(
            [f"# {skill['name']}\n\n{skill['document']}" for skill in skills]
        )

        # 构建 system 消息
        system_content = f"""你是一个多技能助手，请综合运用以下技能文档处理用户请求。

# 技能文档
{combined_documents}
"""

        # 创建 prompt 模板
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_content), ("user", "{user_request}")]
        )

        # 构建 chain
        chain = prompt | self.llm | StrOutputParser()

        return chain

    def build_skill_with_history_chain(
        self, skill_document: str, conversation_history: list[dict[str, str]]
    ) -> Any:
        """
        构建带历史记录的 Chain

        Args:
            skill_document: Skill 文档内容
            conversation_history: 对话历史

        Returns:
            LangChain Runnable Chain
        """
        # 构建 system 消息
        system_content = f"""你是一个技能助手，请按照以下技能文档处理用户请求，并考虑对话历史。

# 技能文档
{skill_document}
"""

        # 创建 prompt 模板，包含历史记录占位符
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_content),
                MessagesPlaceholder(variable_name="history"),
                ("user", "{user_request}"),
            ]
        )

        # 构建 chain
        chain = prompt | self.llm | StrOutputParser()

        return chain

    def _format_context(self, context: dict[str, Any] | None) -> str:
        """
        格式化上下文为字符串

        Args:
            context: 上下文字典

        Returns:
            格式化后的字符串
        """
        if not context:
            return "无额外上下文"

        lines = []
        for key, value in context.items():
            lines.append(f"{key}: {value}")

        return "\n".join(lines)
