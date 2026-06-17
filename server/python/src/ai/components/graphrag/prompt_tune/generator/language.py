"""用于 GraphRAG 提示词的语言检测。

Language detection for GraphRAG prompts.
"""

from ai.components.graphrag.llm.types.llm_types import CompletionLLM
from ai.components.graphrag.prompt_tune.prompt import DETECT_LANGUAGE_PROMPT


async def detect_language(llm: CompletionLLM, docs: str | list[str]) -> str:
    """
    检测输入文档的语言,用于 GraphRAG 提示词。

    Detect input language to use for GraphRAG prompts.

    参数 Parameters
    ----------
    - llm (CompletionLLM): 用于生成的语言模型。The LLM to use for generation
    - docs (str | list[str]): 用于检测语言的文档。The docs to detect language from

    返回 Returns
    -------
    - str: 检测到的语言。The detected language.
    """
    # 如果输入是列表,则将其连接成字符串
    # If input is a list, join it into a string
    docs_str = " ".join(docs) if isinstance(docs, list) else docs

    # 格式化语言检测提示词
    # Format language detection prompt
    language_prompt = DETECT_LANGUAGE_PROMPT.format(input_text=docs_str)

    # 调用 LLM 检测语言
    # Call LLM to detect language
    response = await llm(language_prompt)

    return str(response.output)
