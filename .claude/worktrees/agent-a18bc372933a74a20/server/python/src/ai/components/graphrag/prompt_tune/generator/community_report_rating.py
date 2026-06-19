"""生成社区报告评分的评分描述。

Generate a rating description for community report rating.
"""

from ai.components.graphrag.llm.types.llm_types import CompletionLLM
from ai.components.graphrag.prompt_tune.prompt import (
    GENERATE_REPORT_RATING_PROMPT,
)


async def generate_community_report_rating(
    llm: CompletionLLM, domain: str, persona: str, docs: str | list[str]
) -> str:
    """
    生成用于 GraphRAG 提示词的评分描述。

    Generate an LLM persona to use for GraphRAG prompts.

    参数 Parameters
    ----------
    - llm (CompletionLLM): 用于生成的语言模型。The LLM to use for generation
    - domain (str): 生成评分描述的领域。The domain to generate a rating for
    - persona (str): 生成评分描述的角色人设。The persona to generate a rating for for
    - docs (str | list[str]): 用于评分描述上下文化的文档。Documents used to contextualize the rating

    返回 Returns
    -------
    - str: 生成的评分描述提示词响应。The generated rating description prompt response.
    """
    # 如果输入是列表,则将其连接成字符串
    # If input is a list, join it into a string
    docs_str = " ".join(docs) if isinstance(docs, list) else docs

    # 格式化评分描述生成提示词
    # Format rating description generation prompt
    domain_prompt = GENERATE_REPORT_RATING_PROMPT.format(
        domain=domain, persona=persona, input_text=docs_str
    )

    # 调用 LLM 生成评分描述
    # Call LLM to generate rating description
    response = await llm(domain_prompt)

    return str(response.output).strip()
