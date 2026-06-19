"""社区报告员角色生成器模块。

Community reporter role generator module.
"""

from ai.components.graphrag.llm.types.llm_types import CompletionLLM
from ai.components.graphrag.prompt_tune.prompt import (
    GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT,
)


async def generate_community_reporter_role(
    llm: CompletionLLM, domain: str, persona: str, docs: str | list[str]
) -> str:
    """
    生成用于 GraphRAG 提示词的社区报告员角色人设。

    Generate an LLM persona to use for GraphRAG prompts.

    参数 Parameters
    ----------
    - llm (CompletionLLM): 用于生成的语言模型。The LLM to use for generation
    - domain (str): 生成角色人设的领域。The domain to generate a persona for
    - persona (str): 生成角色人设的基础人设。The persona to generate a role for
    - docs (str | list[str]): 从中生成角色人设的文档。The domain to generate a persona for

    返回 Returns
    -------
    - str: 生成的角色人设提示词响应。The generated domain prompt response.
    """
    # 如果输入是列表,则将其连接成字符串
    # If input is a list, join it into a string
    docs_str = " ".join(docs) if isinstance(docs, list) else docs

    # 格式化角色人设提示词模板
    # Format role persona prompt template
    domain_prompt = GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT.format(
        domain=domain, persona=persona, input_text=docs_str
    )

    # 调用 LLM 生成角色人设
    # Call LLM to generate role persona
    response = await llm(domain_prompt)

    return str(response.output)
