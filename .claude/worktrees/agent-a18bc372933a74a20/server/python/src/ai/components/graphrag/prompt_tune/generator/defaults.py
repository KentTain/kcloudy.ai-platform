"""微调模块的默认值。

Default values for the fine-tuning module.
"""

from ai.components.graphrag.prompt.prompt_tune.generator.zh.defaults import (
    DEFAULT_TASK as DEFAULT_ZH_TASK,
)

# 默认任务模板,用于生成提示词时指定任务描述
# Default task template for specifying task description when generating prompts
DEFAULT_TASK = (
    """
Identify the relations and structure of the community of interest, specifically within the {domain} domain.
"""
    if DEFAULT_ZH_TASK is None
    else DEFAULT_ZH_TASK
)

# 最大 token 数量限制,用于控制生成的提示词长度
# Maximum token count limit for controlling the length of generated prompts
MAX_TOKEN_COUNT = 2000
