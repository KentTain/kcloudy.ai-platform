"""社区报告摘要提示词生成器模块。

Module for generating prompts for community report summarization.
"""

from pathlib import Path

from ai.components.graphrag.prompt_tune.template import (
    COMMUNITY_REPORT_SUMMARIZATION_PROMPT,
)

# 社区摘要提示词文件名
# Community summarization prompt filename
COMMUNITY_SUMMARIZATION_FILENAME = "community_report.txt"


def create_community_summarization_prompt(
    persona: str,
    role: str,
    report_rating_description: str,
    language: str,
    output_path: Path | None = None,
) -> str:
    """
    创建社区摘要提示词。如果提供了 output_path,则将提示词写入文件。

    Create a prompt for community summarization. If output_path is provided, write the prompt to a file.

    参数 Parameters
    ----------
    - persona (str): 用于社区摘要提示词的角色人设。The persona to use for the community summarization prompt
    - role (str): 用于社区摘要提示词的角色。The role to use for the community summarization prompt
    - language (str): 用于社区摘要提示词的语言。The language to use for the community summarization prompt
    - output_path (Path | None): 将提示词写入的路径。默认为 None。如果为 None,则不将提示词写入文件。
                                  The path to write the prompt to. Default is None. If None, the prompt is not written to a file. Default is None.

    返回 Returns
    -------
    - str: 社区摘要提示词。The community summarization prompt
    """
    # 格式化社区摘要提示词
    # Format community summarization prompt
    prompt = COMMUNITY_REPORT_SUMMARIZATION_PROMPT.format(
        persona=persona,
        role=role,
        report_rating_description=report_rating_description,
        language=language,
    )

    # 如果指定了输出路径,则将提示词写入文件
    # If output path is specified, write prompt to file
    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / COMMUNITY_SUMMARIZATION_FILENAME
        # 将文件写入输出路径
        # Write file to output path
        with output_path.open("wb") as file:
            file.write(prompt.encode(encoding="utf-8", errors="strict"))

    return prompt
