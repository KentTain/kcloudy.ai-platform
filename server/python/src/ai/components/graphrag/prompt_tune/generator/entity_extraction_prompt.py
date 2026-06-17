"""实体抽取提示词生成器模块。

Entity Extraction prompt generator module.
"""

from pathlib import Path

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.index.utils.tokens import num_tokens_from_string
from ai.components.graphrag.prompt_tune.template import (
    EXAMPLE_EXTRACTION_TEMPLATE,
    GRAPH_EXTRACTION_JSON_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
    UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE,
    UNTYPED_GRAPH_EXTRACTION_PROMPT,
)

# 实体抽取提示词文件名
# Entity extraction prompt filename
ENTITY_EXTRACTION_FILENAME = "entity_extraction.txt"


def create_entity_extraction_prompt(
    entity_types: str | list[str] | None,
    docs: list[str],
    examples: list[str],
    language: str,
    max_token_count: int,
    encoding_model: str = defs.ENCODING_MODEL,
    json_mode: bool = False,
    output_path: Path | None = None,
    min_examples_required: int = 2,
) -> str:
    """
    创建实体抽取提示词。

    Create a prompt for entity extraction.

    参数 Parameters
    ----------
    - entity_types (str | list[str]): 要抽取的实体类型。The entity types to extract
    - docs (list[str]): 从中抽取实体的文档列表。The list of documents to extract entities from
    - examples (list[str]): 用于实体抽取的示例列表。The list of examples to use for entity extraction
    - language (str): 输入和输出的语言。The language of the inputs and outputs
    - encoding_model (str): 用于 token 计数的模型名称。The name of the model to use for token counting
    - max_token_count (int): 提示词的最大 token 数量。The maximum number of tokens to use for the prompt
    - json_mode (bool): 是否使用 JSON 模式。默认为 False。Whether to use JSON mode for the prompt. Default is False
    - output_path (Path | None): 将提示词写入的路径。默认为 None。The path to write the prompt to. Default is None.
    - min_examples_required (int): 所需的最小示例数量。默认为 2。The minimum number of examples required. Default is 2.

    返回 Returns
    -------
    - str: 实体抽取提示词。The entity extraction prompt
    """
    # 根据实体类型和 json_mode 选择提示词模板
    # Choose prompt template based on entity types and json_mode
    prompt = (
        (GRAPH_EXTRACTION_JSON_PROMPT if json_mode else GRAPH_EXTRACTION_PROMPT)
        if entity_types
        else UNTYPED_GRAPH_EXTRACTION_PROMPT
    )

    # 将实体类型列表转换为字符串
    # Convert entity types list to string
    if isinstance(entity_types, list):
        entity_types = ", ".join(entity_types)

    # 计算剩余可用的 token 数量
    # Calculate remaining available tokens
    tokens_left = (
        max_token_count
        - num_tokens_from_string(prompt, encoding_name=encoding_model)
        - num_tokens_from_string(entity_types, encoding_name=encoding_model)
        if entity_types
        else 0
    )

    examples_prompt = ""

    # 迭代示例,直到没有 token 或没有示例为止
    # Iterate over examples, while we have tokens left or examples left
    for i, output in enumerate(examples):
        input = docs[i]
        # 格式化单个示例
        # Format single example
        example_formatted = (
            EXAMPLE_EXTRACTION_TEMPLATE.format(
                n=i + 1, input_text=input, entity_types=entity_types, output=output
            )
            if entity_types
            else UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE.format(
                n=i + 1, input_text=input, output=output
            )
        )

        # 计算示例的 token 数量
        # Calculate token count for example
        example_tokens = num_tokens_from_string(
            example_formatted, encoding_name=encoding_model
        )

        # 确保至少包含指定数量的示例
        # Ensure at least specified number of examples are included
        if i >= min_examples_required and example_tokens > tokens_left:
            break

        examples_prompt += example_formatted
        tokens_left -= example_tokens

    # 格式化完整的提示词
    # Format complete prompt
    prompt = (
        prompt.format(
            entity_types=entity_types, examples=examples_prompt, language=language
        )
        if entity_types
        else prompt.format(examples=examples_prompt, language=language)
    )

    # 如果指定了输出路径,则将提示词写入文件
    # If output path is specified, write prompt to file
    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / ENTITY_EXTRACTION_FILENAME
        # 将文件写入输出路径
        # Write file to output path
        with output_path.open("wb") as file:
            file.write(prompt.encode(encoding="utf-8", errors="strict"))

    return prompt
