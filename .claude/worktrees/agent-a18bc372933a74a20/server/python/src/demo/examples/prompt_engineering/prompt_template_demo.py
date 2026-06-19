"""
PromptTemplate 基础示例

演示如何使用 LangChain 的 PromptTemplate 创建动态提示词模板。
支持变量替换、部分变量绑定等特性。

Day 3 讲义：AI 智能体应用实战 - 提示词工程
"""

from langchain_core.prompts import PromptTemplate


def create_prompt_template(template: str, input_variables: list[str]) -> PromptTemplate:
    """
    创建基础的 PromptTemplate 实例

    Args:
        template: 包含占位符的模板字符串，如 "你好，{name}！"
        input_variables: 变量名列表，如 ["name"]

    Returns:
        PromptTemplate 实例

    Example:
        >>> template = create_prompt_template("你好，{name}！你是{role}。", ["name", "role"])
        >>> result = template.format(name="小明", role="开发者")
        >>> print(result)
        你好，小明！你是开发者。
    """
    return PromptTemplate(
        template=template,
        input_variables=input_variables,
    )


def create_partial_template(
    template: str, input_variables: list[str], partial_variables: dict
) -> PromptTemplate:
    """
    创建带有部分变量绑定的 PromptTemplate

    部分变量绑定允许你在创建模板时预设一些变量的值，
    后续调用时只需提供剩余变量的值。

    Args:
        template: 模板字符串
        input_variables: 完整的变量名列表
        partial_variables: 要预设的变量及其值

    Returns:
        带有部分变量绑定的 PromptTemplate 实例

    Example:
        >>> template = create_partial_template(
        ...     "你好，{name}！今天是{day}，天气{weather}。",
        ...     ["name", "day", "weather"],
        ...     {"day": "星期一", "weather": "晴朗"}
        ... )
        >>> result = template.format(name="小明")
        >>> print(result)
        你好，小明！今天是星期一，天气晴朗。
    """
    return PromptTemplate(
        template=template,
        input_variables=input_variables,
        partial_variables=partial_variables,
    )


def demo_basic_template() -> None:
    """演示基础模板用法"""
    print("=== 基础 PromptTemplate 示例 ===\n")

    # 示例1：简单变量替换
    template = create_prompt_template(
        template="请用{language}解释什么是{concept}。",
        input_variables=["language", "concept"],
    )

    result = template.format(language="中文", concept="机器学习")
    print(f"生成的提示词：\n{result}\n")

    # 示例2：从模板创建并格式化
    template2 = PromptTemplate.from_template("写一首关于{topic}的{style}诗。")
    result2 = template2.format(topic="春天", style="七言绝句")
    print(f"从模板创建的提示词：\n{result2}\n")


def demo_partial_variables() -> None:
    """演示部分变量绑定"""
    print("=== 部分变量绑定示例 ===\n")

    # 创建带有预设值的模板
    template = create_partial_template(
        template="""
你是一位专业的{domain}专家。
请用{tone}的语气回答以下问题：
{question}

回答要求：
1. 语言简洁明了
2. 提供具体例子
3. 适合{audience}理解
""",
        input_variables=["domain", "tone", "question", "audience"],
        partial_variables={
            "domain": "人工智能",
            "tone": "专业但友好",
            "audience": "初学者",
        },
    )

    # 只需要提供 question 变量
    result = template.format(question="什么是深度学习？")
    print(f"生成的提示词：\n{result}\n")


def demo_template_composition() -> None:
    """演示模板组合"""
    print("=== 模板组合示例 ===\n")

    # 系统提示词模板
    system_template = PromptTemplate.from_template(
        "你是一个{role}，专注于{specialty}。"
    )

    # 用户问题模板
    user_template = PromptTemplate.from_template("请回答：{question}")

    # 组合使用
    system_prompt = system_template.format(role="AI助手", specialty="自然语言处理")
    user_prompt = user_template.format(question="什么是词嵌入？")

    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    print(f"组合后的完整提示词：\n{full_prompt}\n")


if __name__ == "__main__":
    demo_basic_template()
    demo_partial_variables()
    demo_template_composition()
