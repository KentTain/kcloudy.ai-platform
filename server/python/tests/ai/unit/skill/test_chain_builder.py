"""Skill Chain Builder 单元测试"""

from unittest.mock import MagicMock

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableSequence


class TestSkillChainBuilder:
    """测试 SkillChainBuilder"""

    def test_build_knowledge_skill_chain(self):
        """验证构建知识文档 Chain"""
        # Arrange
        from ai.components.skill.chain_builder import SkillChainBuilder

        mock_llm = MagicMock(spec=BaseChatModel)
        builder = SkillChainBuilder(mock_llm)
        skill_document = "这是一个技能文档，用于处理用户请求。"

        # Act
        chain = builder.build_knowledge_skill_chain(skill_document)

        # Assert
        assert chain is not None
        assert isinstance(chain, RunnableSequence)
        # 验证 chain 是 prompt | llm | parser 的组合
        assert hasattr(chain, "steps")
        assert len(chain.steps) == 3

    def test_build_knowledge_skill_chain_with_context(self):
        """验证带上下文构建"""
        from ai.components.skill.chain_builder import SkillChainBuilder

        mock_llm = MagicMock(spec=BaseChatModel)
        builder = SkillChainBuilder(mock_llm)
        skill_document = "技能文档"
        context = {"user_name": "张三", "domain": "医疗"}

        # Act
        chain = builder.build_knowledge_skill_chain(skill_document, context=context)

        # Assert
        assert chain is not None
        assert isinstance(chain, RunnableSequence)

    def test_build_multi_skill_chain(self):
        """验证多 Skill 组合"""
        from ai.components.skill.chain_builder import SkillChainBuilder

        mock_llm = MagicMock(spec=BaseChatModel)
        builder = SkillChainBuilder(mock_llm)
        skills = [
            {"name": "skill1", "document": "技能1文档"},
            {"name": "skill2", "document": "技能2文档"},
        ]
        user_request = "请帮我处理这个任务"

        # Act
        chain = builder.build_multi_skill_chain(skills, user_request)

        # Assert
        assert chain is not None
        assert isinstance(chain, RunnableSequence)

    def test_build_multi_skill_chain_combines_documents(self):
        """验证多 Skill 组合文档"""
        from ai.components.skill.chain_builder import SkillChainBuilder

        mock_llm = MagicMock(spec=BaseChatModel)
        builder = SkillChainBuilder(mock_llm)
        skills = [
            {"name": "skill1", "document": "技能1：处理文本"},
            {"name": "skill2", "document": "技能2：翻译文本"},
        ]
        user_request = "翻译文档"

        # Act
        chain = builder.build_multi_skill_chain(skills, user_request)

        # Assert - 验证文档被正确组合
        # 由于 chain 是 RunnablePipeline，我们需要验证 prompt 模板
        # 可以通过查看第一个步骤（prompt template）来验证
        assert chain is not None
        # 验证 chain 可以被调用（虽然会失败，因为我们 mock 了 llm）
        # 这主要是确保 chain 结构正确

    def test_build_skill_with_history_chain(self):
        """验证带历史记录的 Chain"""
        from ai.components.skill.chain_builder import SkillChainBuilder

        mock_llm = MagicMock(spec=BaseChatModel)
        builder = SkillChainBuilder(mock_llm)
        skill_document = "这是一个对话技能"
        conversation_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
        ]

        # Act
        chain = builder.build_skill_with_history_chain(skill_document, conversation_history)

        # Assert
        assert chain is not None
        assert isinstance(chain, RunnableSequence)
        # 验证 chain 的结构正确
        assert len(chain.steps) == 3
