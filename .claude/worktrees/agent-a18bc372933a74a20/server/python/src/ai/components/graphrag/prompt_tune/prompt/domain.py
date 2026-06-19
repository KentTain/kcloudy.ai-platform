"""领域生成的微调提示词模板。

Fine-tuning prompts for domain generation.
"""

from ai.components.graphrag.prompt.prompt_tune.prompt.zh.domain import (
    GENERATE_DOMAIN_PROMPT as GENERATE_ZH_DOMAIN_PROMPT,
)

# 领域生成提示词模板
# Domain generation prompt template
GENERATE_DOMAIN_PROMPT = (
    """
You are an intelligent assistant that helps a human to analyze the information in a text document.
Given a sample text, help the user by assigning a descriptive domain that summarizes what the text is about.
Example domains are: "Social studies", "Algorithmic analysis", "Medical science", among others.

Text: {input_text}
Domain:"""
    if GENERATE_ZH_DOMAIN_PROMPT is None
    else GENERATE_ZH_DOMAIN_PROMPT
)
