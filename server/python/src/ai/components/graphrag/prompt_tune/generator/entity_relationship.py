"""实体关系示例生成模块。

Entity relationship example generation module.
"""

import asyncio
import json

from ai.components.graphrag.llm.types.llm_types import CompletionLLM
from ai.components.graphrag.prompt_tune.prompt import (
    ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT,
    ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
    UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
)

# 最大示例数量限制
# Maximum number of examples
MAX_EXAMPLES = 5


async def generate_entity_relationship_examples(
    llm: CompletionLLM,
    persona: str,
    entity_types: str | list[str] | None,
    docs: str | list[str],
    language: str,
    json_mode: bool = False,
) -> list[str]:
    """
    生成实体/关系示例列表,用于生成实体配置。

    根据 json_mode 参数,返回 JSON 格式或 tuple_delimiter 格式的实体/关系示例。

    Generate a list of entity/relationships examples for use in generating an entity configuration.

    Will return entity/relationships examples as either JSON or in tuple_delimiter format depending
    on the json_mode parameter.

    参数 Parameters
    ----------
    - llm (CompletionLLM): 用于生成的语言模型。The LLM to use for generation
    - persona (str): 用于生成的角色人设。The persona to use for generation
    - entity_types (str | list[str] | None): 实体类型。The entity types
    - docs (str | list[str]): 从中生成示例的文档。The documents to generate examples from
    - language (str): 输入和输出的语言。The language of inputs and outputs
    - json_mode (bool): 是否使用 JSON 模式。默认为 False。Whether to use JSON mode. Default is False

    返回 Returns
    -------
    - list[str]: 实体/关系示例列表。The list of entity/relationships examples
    """
    # 将文档转换为列表
    # Convert documents to list
    docs_list = [docs] if isinstance(docs, str) else docs

    # 构建历史消息,将角色人设作为系统消息
    # Build history messages, with persona as system message
    history = [{"role": "system", "content": persona}]

    # 根据是否提供实体类型选择提示词模板
    # Choose prompt template based on whether entity types are provided
    if entity_types:
        # 将实体类型转换为字符串
        # Convert entity types to string
        entity_types_str = (
            entity_types if isinstance(entity_types, str) else ", ".join(entity_types)
        )

        # 为每个文档构建提示词消息
        # Build prompt messages for each document
        messages = [
            (
                ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT
                if json_mode
                else ENTITY_RELATIONSHIPS_GENERATION_PROMPT
            ).format(entity_types=entity_types_str, input_text=doc, language=language)
            for doc in docs_list
        ]
    else:
        # 使用无类型实体关系生成提示词
        # Use untyped entity relationship generation prompt
        messages = [
            UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT.format(
                input_text=doc, language=language
            )
            for doc in docs_list
        ]

    # 限制消息数量不超过最大示例数
    # Limit message count to maximum examples
    messages = messages[:MAX_EXAMPLES]

    # 为每个消息创建 LLM 任务
    # Create LLM tasks for each message
    tasks = [llm(message, history=history, json=json_mode) for message in messages]

    # 并发执行所有 LLM 任务
    # Execute all LLM tasks concurrently
    responses = await asyncio.gather(*tasks)

    # 根据 json_mode 格式化返回结果
    # Format return results based on json_mode
    return [
        json.dumps(response.json or "", ensure_ascii=False)
        if json_mode
        else str(response.output)
        for response in responses
    ]
