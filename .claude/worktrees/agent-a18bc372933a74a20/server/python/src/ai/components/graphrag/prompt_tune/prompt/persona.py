"""角色人设生成的微调提示词模板。

Fine-tuning prompts for persona generation.
"""

from ai.components.graphrag.prompt.prompt_tune.prompt.zh.persona import (
    GENERATE_PERSONA_PROMPT as GENERATE_PERSONA_PROMPT_ZH,
)

# 角色人设生成提示词模板
# Persona generation prompt template
GENERATE_PERSONA_PROMPT = (
    """
You are an intelligent assistant that helps a human to analyze the information in a text document.
Given a specific type of task and sample text, help the user by generating a 3 to 4 sentence description of an expert who could help solve the problem.
Use a format similar to the following:
You are an expert {{role}}. You are skilled at {{relevant skills}}. You are adept at helping people with {{specific task}}.

task: {sample_task}
persona description:"""
    if GENERATE_PERSONA_PROMPT_ZH is None
    else GENERATE_PERSONA_PROMPT_ZH
)
