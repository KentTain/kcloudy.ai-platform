"""
FewShotPromptTemplate 少样本学习示例

演示如何使用 LangChain 的 FewShotPromptTemplate 创建少样本学习提示词。
通过提供示例来引导模型生成期望格式的输出。

Day 3 讲义：AI 智能体应用实战 - 提示词工程
"""

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


def create_few_shot_prompt(
    examples: list[dict],
    example_prompt: PromptTemplate,
    prefix: str = "",
    suffix: str = "",
    input_variables: list[str] | None = None,
) -> FewShotPromptTemplate:
    """
    创建少样本学习提示词模板

    Args:
        examples: 示例列表，每个示例是一个字典
        example_prompt: 用于格式化单个示例的模板
        prefix: 前缀文本，放在所有示例之前
        suffix: 后缀文本，放在所有示例之后，通常包含输入占位符
        input_variables: 输入变量列表

    Returns:
        FewShotPromptTemplate 实例

    Example:
        >>> examples = [
        ...     {"input": "快乐", "output": "悲伤"},
        ...     {"input": "高大", "output": "矮小"},
        ... ]
        >>> example_prompt = PromptTemplate(
        ...     template="输入: {input}\\n输出: {output}",
        ...     input_variables=["input", "output"],
        ... )
        >>> few_shot = create_few_shot_prompt(
        ...     examples=examples,
        ...     example_prompt=example_prompt,
        ...     prefix="请写出下列词语的反义词：",
        ...     suffix="输入: {input}\\n输出:",
        ...     input_variables=["input"],
        ... )
        >>> result = few_shot.format(input="明亮")
    """
    return FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix=prefix,
        suffix=suffix,
        input_variables=input_variables or [],
    )


def create_example_selector(
    examples: list[dict],
    embedding_model: OpenAIEmbeddings | None = None,
    k: int = 2,
) -> SemanticSimilarityExampleSelector:
    """
    创建语义相似度示例选择器

    根据输入与示例的语义相似度动态选择最相关的示例。

    Args:
        examples: 示例列表
        embedding_model: 嵌入模型，默认使用 OpenAIEmbeddings
        k: 选择的示例数量

    Returns:
        SemanticSimilarityExampleSelector 实例

    Note:
        需要 OpenAI API Key 或配置了其他嵌入模型
    """
    if embedding_model is None:
        embedding_model = OpenAIEmbeddings()

    # 创建向量存储用于语义搜索
    to_vectorize = [" ".join(example.values()) for example in examples]
    vectorstore = FAISS.from_texts(to_vectorize, embedding_model)

    return SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=k,
    )


def demo_basic_few_shot() -> None:
    """演示基础少样本学习"""
    print("=== 基础 FewShotPromptTemplate 示例 ===\n")

    # 定义示例
    examples = [
        {"input": "快乐", "output": "悲伤"},
        {"input": "高大", "output": "矮小"},
        {"input": "炎热", "output": "寒冷"},
    ]

    # 定义示例格式模板
    example_prompt = PromptTemplate(
        template="输入: {input}\n输出: {output}",
        input_variables=["input", "output"],
    )

    # 创建少样本提示词
    few_shot_prompt = create_few_shot_prompt(
        examples=examples,
        example_prompt=example_prompt,
        prefix="请写出下列词语的反义词：\n",
        suffix="输入: {input}\n输出:",
        input_variables=["input"],
    )

    # 使用模板
    result = few_shot_prompt.format(input="明亮")
    print(f"生成的提示词：\n{result}\n")


def demo_sentiment_analysis() -> None:
    """演示情感分析任务"""
    print("=== 情感分析少样本示例 ===\n")

    # 情感分析示例
    examples = [
        {
            "review": "这家餐厅的服务态度很好，菜品也很美味！",
            "sentiment": "正面",
            "reason": "提到了服务态度好和菜品美味",
        },
        {
            "review": "等了一个小时才上菜，太失望了。",
            "sentiment": "负面",
            "reason": "抱怨等待时间过长",
        },
        {
            "review": "环境一般，价格适中，无功无过。",
            "sentiment": "中性",
            "reason": "描述平淡，没有明显的情感倾向",
        },
    ]

    example_prompt = PromptTemplate(
        template="评价：{review}\n情感：{sentiment}\n理由：{reason}",
        input_variables=["review", "sentiment", "reason"],
    )

    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix="请分析以下餐厅评价的情感倾向：\n",
        suffix="评价：{review}\n情感：\n理由：",
        input_variables=["review"],
    )

    result = few_shot_prompt.format(review="服务员很热情，推荐的红烧肉很好吃！")
    print(f"生成的提示词：\n{result}\n")


def demo_structured_output() -> None:
    """演示结构化输出"""
    print("=== 结构化输出少样本示例 ===\n")

    # 实体抽取示例
    examples = [
        {
            "text": "苹果公司在2024年发布了新款iPhone。",
            "entities": "公司：苹果公司\n产品：iPhone\n时间：2024年",
        },
        {
            "text": "马斯克的SpaceX成功发射了星舰火箭。",
            "entities": "人物：马斯克\n公司：SpaceX\n产品：星舰火箭",
        },
    ]

    example_prompt = PromptTemplate(
        template="文本：{text}\n实体：\n{entities}",
        input_variables=["text", "entities"],
    )

    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix="从下列文本中提取关键实体（人物、公司、产品、时间等）：\n",
        suffix="文本：{text}\n实体：\n",
        input_variables=["text"],
    )

    result = few_shot_prompt.format(text="比尔·盖茨在1975年创立了微软。")
    print(f"生成的提示词：\n{result}\n")


if __name__ == "__main__":
    demo_basic_few_shot()
    demo_sentiment_analysis()
    demo_structured_output()
