"""Skill Context Manager - 管理 Skill 执行上下文"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ai.components.skill.chain_builder import SkillChainBuilder


@dataclass
class SkillExecutionContext:
    """Skill 执行上下文"""

    skill_id: str
    skill_name: str
    skill_type: str  # knowledge | script
    user_id: str
    tenant_id: str
    conversation_id: str
    message_history: list[dict[str, str]] = field(default_factory=list)
    skill_document: str = ""
    examples: dict[str, str] = field(default_factory=dict)
    loaded_at: datetime = field(default_factory=datetime.now)
    invoke_count: int = 0
    last_invoked_at: datetime | None = None
    chain_cache: dict[str, Any] = field(default_factory=dict)


class SkillContextManager:
    """
    Skill 上下文管理器

    管理 Skill 的执行上下文和 Chain 缓存
    """

    def __init__(self):
        """初始化上下文管理器"""
        self._contexts: dict[str, SkillExecutionContext] = {}
        self._llm: Any = None

    def set_llm(self, llm: Any) -> None:
        """
        设置 LLM 实例

        Args:
            llm: LangChain LLM 实例
        """
        self._llm = llm

    def _build_context_key(self, tenant_id: str, user_id: str, skill_id: str) -> str:
        """
        构建上下文键

        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            skill_id: Skill ID

        Returns:
            上下文键字符串
        """
        return f"{tenant_id}:{user_id}:{skill_id}"

    def load_skill(
        self,
        skill_id: str,
        user_id: str,
        tenant_id: str,
        conversation_id: str,
        skill_document: str = "",
        examples: dict[str, str] | None = None,
        skill_name: str = "",
        skill_type: str = "knowledge",
    ) -> SkillExecutionContext:
        """
        加载 Skill 并创建上下文

        Args:
            skill_id: Skill ID
            user_id: 用户 ID
            tenant_id: 租户 ID
            conversation_id: 对话 ID
            skill_document: Skill 文档
            examples: 示例字典
            skill_name: Skill 名称
            skill_type: Skill 类型

        Returns:
            Skill 执行上下文
        """
        key = self._build_context_key(tenant_id, user_id, skill_id)

        # 创建上下文
        context = SkillExecutionContext(
            skill_id=skill_id,
            skill_name=skill_name or skill_id,
            skill_type=skill_type,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            skill_document=skill_document,
            examples=examples or {},
        )

        # 缓存上下文
        self._contexts[key] = context

        return context

    async def invoke_skill(
        self,
        skill_id: str,
        user_request: str,
        context: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """
        调用 Skill

        Args:
            skill_id: Skill ID
            user_request: 用户请求
            context: 上下文信息
            tenant_id: 租户 ID
            user_id: 用户 ID

        Returns:
            Skill 执行结果

        Raises:
            RuntimeError: Skill 未加载
        """
        # 构建上下文键
        if not tenant_id or not user_id:
            raise ValueError("tenant_id and user_id are required")

        key = self._build_context_key(tenant_id, user_id, skill_id)

        # 获取上下文
        if key not in self._contexts:
            raise RuntimeError(f"Skill not loaded: {skill_id}")

        skill_context = self._contexts[key]

        # 获取或构建 Chain
        chain = self._get_or_build_chain(skill_context)

        # 更新统计信息（在调用前记录，无论成功或失败）
        skill_context.invoke_count += 1
        skill_context.last_invoked_at = datetime.now()

        # 执行 Chain
        result = await chain.ainvoke({"user_request": user_request})

        return result

    def _get_or_build_chain(self, context: SkillExecutionContext) -> Any:
        """
        获取或构建 Chain

        Args:
            context: Skill 执行上下文

        Returns:
            LangChain Runnable Chain
        """
        # 检查缓存
        cache_key = "default"
        if cache_key in context.chain_cache:
            return context.chain_cache[cache_key]

        # 检查 LLM
        if not self._llm:
            raise RuntimeError("LLM not set. Call set_llm() first.")

        # 构建 Chain
        builder = SkillChainBuilder(self._llm)
        examples_str = self._format_examples(context.examples)

        chain = builder.build_knowledge_skill_chain(
            skill_document=context.skill_document,
            examples=examples_str,
            context=None,
        )

        # 缓存 Chain
        context.chain_cache[cache_key] = chain

        return chain

    def _format_examples(self, examples: dict[str, str] | None) -> str:
        """
        格式化示例文档

        Args:
            examples: 示例字典

        Returns:
            格式化后的字符串
        """
        if not examples:
            return ""

        lines = []
        for name, content in examples.items():
            lines.append(f"{name}: {content}")

        return "\n".join(lines)

    def _format_context(self, context: dict[str, Any] | None) -> str:
        """
        格式化上下文

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

    def unload_skill(
        self, skill_id: str, tenant_id: str | None = None, user_id: str | None = None
    ) -> None:
        """
        卸载 Skill

        Args:
            skill_id: Skill ID
            tenant_id: 租户 ID
            user_id: 用户 ID
        """
        if not tenant_id or not user_id:
            # 如果没有提供 tenant_id 或 user_id，清除所有匹配的上下文
            keys_to_remove = [
                k for k in self._contexts.keys() if k.endswith(f":{skill_id}")
            ]
            for key in keys_to_remove:
                del self._contexts[key]
        else:
            key = self._build_context_key(tenant_id, user_id, skill_id)
            if key in self._contexts:
                del self._contexts[key]


# 单例实例
skill_context_manager = SkillContextManager()
