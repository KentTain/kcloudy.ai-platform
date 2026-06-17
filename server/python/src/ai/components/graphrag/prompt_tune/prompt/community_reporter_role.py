"""社区报告员角色生成的微调提示词模板。

Fine-tuning prompts for community reporter role generation.
"""

from ai.components.graphrag.prompt.prompt_tune.prompt.zh.community_reporter_role import (
    GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT as GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT_ZH,
)

# 社区报告员角色生成提示词模板
# Community reporter role generation prompt template
GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT = (
    """
{persona}
Given a sample text, help the user by creating a role definition that will be tasked with community analysis.
Take a look at this example, determine its key parts, and using the domain provided and your expertise, create a new role definition for the provided inputs that follows the same pattern as the example.
Remember, your output should look just like the provided example in structure and content.

Example:
A technologist reporter that is analyzing Kevin Scott's "Behind the Tech Podcast", given a list of entities
that belong to the community as well as their relationships and optional associated claims.
The report will be used to inform decision-makers about significant developments associated with the community and their potential impact.


Domain: {domain}
Text: {input_text}
Role:"""
    if GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT_ZH is None
    else GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT_ZH
)
