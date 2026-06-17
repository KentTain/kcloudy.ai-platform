"""语言检测的微调提示词模板。

Fine-tuning prompts for language detection.
"""

from ai.components.graphrag.prompt.prompt_tune.prompt.zh.language import (
    DETECT_LANGUAGE_PROMPT as ZH_DETECT_LANGUAGE_PROMPT,
)

# 语言检测提示词模板
# Language detection prompt template
DETECT_LANGUAGE_PROMPT = (
    """
You are an intelligent assistant that helps a human to analyze the information in a text document.
Given a sample text, help the user by determining what's the primary language of the provided texts.
Examples are: "English", "Spanish", "Japanese", "Portuguese" among others.

Text: {input_text}
Language:"""
    if ZH_DETECT_LANGUAGE_PROMPT is None
    else ZH_DETECT_LANGUAGE_PROMPT
)
