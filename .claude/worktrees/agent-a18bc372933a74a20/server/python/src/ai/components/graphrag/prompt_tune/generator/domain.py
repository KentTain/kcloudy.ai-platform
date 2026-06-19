"""用于 GraphRAG 提示词的领域生成。

Domain generation for GraphRAG prompts.
"""

from ai.components.graphrag.llm.types.llm_types import CompletionLLM
from ai.components.graphrag.prompt_tune.prompt.domain import GENERATE_DOMAIN_PROMPT


async def generate_domain(llm: CompletionLLM, docs: str | list[str]) -> str:
    """
    生成用于 GraphRAG 提示词的领域描述。

    Generate an LLM persona to use for GraphRAG prompts.

    参数 Parameters
    ----------
    - llm (CompletionLLM): 用于生成的语言模型。The LLM to use for generation
    - docs (str | list[str]): 从中生成领域描述的文档。The domain to generate a persona for

    返回 Returns
    -------
    - str: 生成的领域提示词响应。The generated domain prompt response.
    """
    # 如果输入是列表,则将其连接成字符串
    # If input is a list, join it into a string
    docs_str = " ".join(docs) if isinstance(docs, list) else docs

    # 格式化领域生成提示词
    # Format domain generation prompt
    domain_prompt = GENERATE_DOMAIN_PROMPT.format(input_text=docs_str)

    # 调用 LLM 生成领域描述
    # Call LLM to generate domain description
    response = await llm(domain_prompt)

    return str(response.output)
