"""
提示词工程示例模块

演示 LangChain 提示词工程技术：
- PromptTemplate: 动态提示词模板
- FewShotPromptTemplate: 少样本学习提示词
- Output Parser: 结构化输出解析
"""

from demo.examples.prompt_engineering.few_shot_demo import (
    create_example_selector,
    create_few_shot_prompt,
)
from demo.examples.prompt_engineering.output_parser_demo import (
    JsonParserDemo,
    PydanticParserDemo,
)
from demo.examples.prompt_engineering.prompt_template_demo import (
    create_partial_template,
    create_prompt_template,
)

__all__ = [
    "create_prompt_template",
    "create_partial_template",
    "create_few_shot_prompt",
    "create_example_selector",
    "PydanticParserDemo",
    "JsonParserDemo",
]
