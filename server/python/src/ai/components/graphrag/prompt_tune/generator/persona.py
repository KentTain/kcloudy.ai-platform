"""用于微调 GraphRAG 提示词的角色人设生成模块。

Persona generating module for fine-tuning GraphRAG prompts.
"""

from ai.components.graphrag.llm.types.llm_types import CompletionLLM
from ai.components.graphrag.prompt_tune.generator.defaults import DEFAULT_TASK
from ai.components.graphrag.prompt_tune.prompt import GENERATE_PERSONA_PROMPT


async def generate_persona(
    llm: CompletionLLM, domain: str, task: str = DEFAULT_TASK
) -> str:
    """
    生成用于 GraphRAG 提示词的角色人设。

    Generate an LLM persona to use for GraphRAG prompts.

    参数 Parameters
    ----------
    - llm (CompletionLLM): 用于生成的语言模型。The LLM to use for generation
    - domain (str): 生成角色人设的领域。The domain to generate a persona for
    - task (str): 生成角色人设的任务。默认为 DEFAULT_TASK。The task to generate a persona for. Default is DEFAULT_TASK
    """
    # 格式化任务模板,将领域信息填充到任务描述中
    # Format task template, filling domain information into task description
    formatted_task = task.format(domain=domain)

    # 格式化角色人设生成提示词
    # Format persona generation prompt
    persona_prompt = GENERATE_PERSONA_PROMPT.format(sample_task=formatted_task)

    # 调用 LLM 生成角色人设
    # Call LLM to generate persona
    response = await llm(persona_prompt)

    return str(response.output)
