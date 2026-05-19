"""LangChain 文本总结策略测试

测试三种文本总结策略：
1. Stuff: 一次性将所有内容输入给大模型
2. Map-Reduce: 先分块总结，再合并总结
3. Refine: 迭代优化总结

注意：这是结构演示测试，使用模拟数据，不依赖实际 LLM 服务。
"""

import pytest
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class LLMUsage:
    """LLM token 使用统计"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


async def stuff_summarize(content: str) -> tuple[str, LLMUsage]:
    """Stuff 策略：一次性将所有内容输入给大模型

    原理：
    - 将整个文本直接塞进 prompt
    - 单次 LLM 调用生成总结
    - 优点：简单快速，信息完整
    - 缺点：受 context window 限制，不适合超长文本
    """
    # 模拟 LLM 调用（实际项目中替换为真实 LLM）
    summary = "这是 Stuff 策略生成的总结示例（模拟返回）"
    usage = LLMUsage(
        prompt_tokens=len(content) // 4,
        completion_tokens=50,
        total_tokens=len(content) // 4 + 50,
    )
    return summary, usage


async def map_reduce_summarize(
    content: str, chunk_size: int = 1000
) -> tuple[str, LLMUsage, int]:
    """Map-Reduce 策略：先分块总结，再合并总结

    原理：
    - Map 阶段：将长文档分成多个 chunk，每个 chunk 分别调用 LLM 生成总结
    - Reduce 阶段：将所有 chunk 的总结合并，再次调用 LLM 生成最终总结
    - 优点：可处理超长文档，可并行化
    - 缺点：可能丢失跨 chunk 的上下文信息，需要多次 LLM 调用

    Returns:
        tuple[str, LLMUsage, int]: 摘要文本、LLM 用量、分块数量
    """
    # 分切文档
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    )
    docs = text_splitter.create_documents([content])
    chunk_count = len(docs)

    # 模拟返回结果
    summary = "这是 Map-Reduce 策略生成的总结示例（模拟返回）"
    usage = LLMUsage(
        prompt_tokens=len(content) // 4,
        completion_tokens=100,
        total_tokens=len(content) // 4 + 100,
    )

    return summary, usage, chunk_count


async def refine_summarize(
    content: str, chunk_size: int = 1000
) -> tuple[str, LLMUsage, int]:
    """Refine 策略：迭代优化总结

    原理：
    - 将长文本分成多个 chunk
    - 对第一个 chunk 生成初始总结
    - 将已有总结和下一个 chunk 合并，迭代优化总结
    - 直到处理完所有 chunk
    - 优点：信息保留最完整，前后连贯
    - 缺点：顺序执行，无法并行，调用次数多

    Returns:
        tuple[str, LLMUsage, int]: 摘要文本、LLM 用量、分块数量
    """
    # 分切文档
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    )
    docs = text_splitter.create_documents([content])
    chunk_count = len(docs)

    # 模拟返回结果
    summary = "这是 Refine 策略生成的总结示例（模拟返回）"
    usage = LLMUsage(
        prompt_tokens=len(content) // 4,
        completion_tokens=150,
        total_tokens=len(content) // 4 + 150,
    )

    return summary, usage, chunk_count


@pytest.fixture
def sample_text() -> str:
    """测试文本 fixture"""
    return """
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

人工智能的发展历史可以追溯到20世纪50年代。1956年，在达特茅斯会议上，
约翰·麦卡锡首次提出了"人工智能"这一术语。从那时起，AI经历了多次发展浪潮，
包括符号主义、连接主义和行为主义等不同范式的兴起与衰落。

进入21世纪，随着大数据、云计算和深度学习技术的突破，人工智能迎来了新的发展机遇。
深度学习技术使得机器在图像识别、语音识别、自然语言处理等领域的表现大幅提升，
甚至在某些任务上超越了人类水平。

如今，人工智能已经广泛应用于各个领域，包括医疗诊断、金融风控、智能制造、
自动驾驶、智能客服等。AI技术的发展正在深刻改变着人类的生产和生活方式。
    """


@pytest.mark.asyncio
async def test_stuff_strategy(sample_text: str):
    """测试 Stuff 策略：一次性处理所有内容"""
    print("\n" + "=" * 60)
    print("测试 Stuff 策略（一次性处理）")
    print("=" * 60)

    summary, usage = await stuff_summarize(sample_text)

    print(f"输入长度: {len(sample_text)} 字符")
    print(f"摘要: {summary}")
    print(
        f"用量: Prompt={usage.prompt_tokens}, Completion={usage.completion_tokens}, Total={usage.total_tokens}"
    )

    # 验证返回值
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens


@pytest.mark.asyncio
async def test_map_reduce_strategy(sample_text: str):
    """测试 Map-Reduce 策略：分块处理后合并"""
    print("\n" + "=" * 60)
    print("测试 Map-Reduce 策略（分治合并）")
    print("=" * 60)

    summary, usage, chunk_count = await map_reduce_summarize(
        sample_text, chunk_size=500
    )

    print(f"输入长度: {len(sample_text)} 字符")
    print(f"分块数量: {chunk_count}")
    print(f"摘要: {summary}")
    print(
        f"用量: Prompt={usage.prompt_tokens}, Completion={usage.completion_tokens}, Total={usage.total_tokens}"
    )

    # 验证返回值
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert chunk_count >= 1, "应该至少有一个分块"
    assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens


@pytest.mark.asyncio
async def test_refine_strategy(sample_text: str):
    """测试 Refine 策略：迭代优化"""
    print("\n" + "=" * 60)
    print("测试 Refine 策略（迭代优化）")
    print("=" * 60)

    summary, usage, chunk_count = await refine_summarize(sample_text, chunk_size=500)

    print(f"输入长度: {len(sample_text)} 字符")
    print(f"分块数量: {chunk_count}")
    print(f"摘要: {summary}")
    print(
        f"用量: Prompt={usage.prompt_tokens}, Completion={usage.completion_tokens}, Total={usage.total_tokens}"
    )

    # 验证返回值
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert chunk_count >= 1, "应该至少有一个分块"
    assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens


@pytest.mark.asyncio
async def test_map_reduce_with_different_chunk_sizes(sample_text: str):
    """测试不同分块大小对 Map-Reduce 的影响"""
    print("\n" + "=" * 60)
    print("测试不同分块大小")
    print("=" * 60)

    chunk_sizes = [200, 500, 1000]
    results = {}

    for chunk_size in chunk_sizes:
        _, _, chunk_count = await map_reduce_summarize(
            sample_text, chunk_size=chunk_size
        )
        results[chunk_size] = chunk_count
        print(f"分块大小 {chunk_size}: {chunk_count} 个分块")

    # 验证：分块大小越小，分块数量越多
    assert results[200] >= results[500] >= results[1000]


@pytest.mark.asyncio
async def test_text_splitter_basic():
    """测试文本分切器基本功能"""
    text = "这是第一句话。这是第二句话。这是第三句话。"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=20,
        chunk_overlap=5,
        separators=["。", " ", ""],
    )

    docs = text_splitter.create_documents([text])

    print(f"\n原始文本: {text}")
    print(f"分块数量: {len(docs)}")
    for i, doc in enumerate(docs):
        print(f"  分块 {i + 1}: {doc.page_content}")

    assert len(docs) >= 1


@pytest.mark.asyncio
async def test_llm_usage_calculation():
    """测试 LLM 用量计算"""
    usage = LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)

    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 50
    assert usage.total_tokens == 150


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
