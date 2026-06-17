"""微调的实体类型生成模块。

Entity type generation module for fine-tuning.
"""

from ai.components.graphrag.llm.types.llm_types import CompletionLLM
from ai.components.graphrag.prompt_tune.generator.defaults import DEFAULT_TASK
from ai.components.graphrag.prompt_tune.prompt.entity_types import (
    ENTITY_TYPE_GENERATION_JSON_PROMPT,
    ENTITY_TYPE_GENERATION_PROMPT,
)


async def generate_entity_types(
    llm: CompletionLLM,
    domain: str,
    persona: str,
    docs: str | list[str],
    task: str = DEFAULT_TASK,
    json_mode: bool = False,
) -> str | list[str]:
    """
    从给定的(小型)文档集合中生成实体类型类别。

    Generate entity type categories from a given set of (small) documents.

    示例输出 Example Output:
    "entity_types": ['military unit', 'organization', 'person', 'location', 'event', 'date', 'equipment']

    参数 Parameters
    ----------
    - llm (CompletionLLM): 用于生成的语言模型。The LLM to use for generation
    - domain (str): 生成实体类型的领域。The domain to generate entity types for
    - persona (str): 用于生成实体类型的角色人设。The persona to use for entity types generation
    - docs (str | list[str]): 从中生成实体类型的文档。The documents to generate entity types from
    - task (str): 生成实体类型的任务。默认为 DEFAULT_TASK。The task to generate entity types for. Default is DEFAULT_TASK
    - json_mode (bool): 是否使用 JSON 模式。默认为 False。Whether to use JSON mode. Default is False

    返回 Returns
    -------
    - str | list[str]: 生成的实体类型,字符串或列表。The generated entity types, string or list
    """
    # 格式化任务模板,将领域信息填充到任务描述中
    # Format task template, filling domain information into task description
    formatted_task = task.format(domain=domain)

    # 将文档列表连接成字符串
    # Join document list into a string
    docs_str = "\n".join(docs) if isinstance(docs, list) else docs

    # 根据 json_mode 选择提示词模板并格式化
    # Choose prompt template based on json_mode and format it
    entity_types_prompt = (
        ENTITY_TYPE_GENERATION_JSON_PROMPT
        if json_mode
        else ENTITY_TYPE_GENERATION_PROMPT
    ).format(task=formatted_task, input_text=docs_str)

    # 构建历史消息,将角色人设作为系统消息
    # Build history messages, with persona as system message
    history = [{"role": "system", "content": persona}]

    # 调用 LLM 生成实体类型
    # Call LLM to generate entity types
    response = await llm(entity_types_prompt, history=history, json=json_mode)

    # 如果是 JSON 模式,提取实体类型列表
    # If JSON mode, extract entity types list
    if json_mode:
        return (response.json or {}).get("entity_types", [])

    return str(response.output)
