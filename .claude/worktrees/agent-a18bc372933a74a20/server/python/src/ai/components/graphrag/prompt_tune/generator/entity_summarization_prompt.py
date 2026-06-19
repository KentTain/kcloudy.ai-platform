"""实体摘要提示词生成器模块。

Entity summarization prompt generation module.
"""

from pathlib import Path

from ai.components.graphrag.prompt_tune.template import ENTITY_SUMMARIZATION_PROMPT

# 实体摘要提示词文件名
# Entity summarization prompt filename
ENTITY_SUMMARIZATION_FILENAME = "summarize_descriptions.txt"


def create_entity_summarization_prompt(
    persona: str,
    language: str,
    output_path: Path | None = None,
) -> str:
    """
    创建实体摘要提示词。

    Create a prompt for entity summarization.

    参数 Parameters
    ----------
    - persona (str): 用于实体摘要提示词的角色人设。The persona to use for the entity summarization prompt
    - language (str): 用于实体摘要提示词的语言。The language to use for the entity summarization prompt
    - output_path (Path | None): 将提示词写入的路径。默认为 None。The path to write the prompt to. Default is None.
    """
    # 格式化实体摘要提示词
    # Format entity summarization prompt
    prompt = ENTITY_SUMMARIZATION_PROMPT.format(persona=persona, language=language)

    # 如果指定了输出路径,则将提示词写入文件
    # If output path is specified, write prompt to file
    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / ENTITY_SUMMARIZATION_FILENAME
        # 将文件写入输出路径
        # Write file to output path
        with output_path.open("wb") as file:
            file.write(prompt.encode(encoding="utf-8", errors="strict"))

    return prompt
