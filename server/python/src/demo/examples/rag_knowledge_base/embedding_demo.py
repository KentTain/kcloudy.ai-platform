"""
Embedding 生成示例

演示如何将文本转换为高维向量：
- 使用 HuggingFace sentence-transformers
- Mock Embedding（用于测试）
- 批量向量生成

示例使用：
    embedder = EmbeddingDemo()
    vector = embedder.embed("Hello World")
    vectors = embedder.embed_batch(["text1", "text2"])
"""

import hashlib
import math
from typing import Any


class MockEmbedding:
    """Mock Embedding 类，用于测试

    使用简单的哈希算法生成确定性向量，
    无需加载真实模型，适合单元测试和演示。
    """

    def __init__(self, dimension: int = 384) -> None:
        """初始化 Mock Embedding

        Args:
            dimension: 向量维度（默认 384，与 BGE-m3 一致）
        """
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        """生成文本向量

        Args:
            text: 输入文本

        Returns:
            归一化的向量列表
        """
        # 使用哈希生成确定性向量
        hash_bytes = hashlib.sha256(text.encode()).digest()
        vector: list[float] = []

        for i in range(self.dimension):
            # 从哈希值派生每个维度
            byte_index = (i * 4) % len(hash_bytes)
            value = int.from_bytes(
                hash_bytes[byte_index : byte_index + 4],
                byteorder="little",
                signed=True,
            )
            vector.append(float(value))

        # 归一化
        return self._normalize(vector)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        return [self.embed(text) for text in texts]

    def _normalize(self, vector: list[float]) -> list[float]:
        """归一化向量

        Args:
            vector: 原始向量

        Returns:
            归一化后的向量
        """
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return vector
        return [x / norm for x in vector]


class EmbeddingDemo:
    """Embedding 演示类

    演示功能：
    - 文本向量生成
    - 批量向量生成
    - 向量相似度计算
    """

    def __init__(
        self,
        model_name: str = "mock",
        dimension: int = 384,
    ) -> None:
        """初始化 Embedding 演示

        Args:
            model_name: 模型名称（"mock" 使用 Mock Embedding）
            dimension: 向量维度
        """
        self.model_name = model_name
        self.dimension = dimension
        self._embedder: MockEmbedding | None = None

    @property
    def embedder(self) -> MockEmbedding:
        """获取 Embedder 实例"""
        if self._embedder is None:
            self._embedder = MockEmbedding(dimension=self.dimension)
        return self._embedder

    def embed(self, text: str) -> list[float]:
        """生成文本向量

        Args:
            text: 输入文本

        Returns:
            向量表示
        """
        return self.embedder.embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        return self.embedder.embed_batch(texts)

    def similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """计算向量余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度（-1 到 1）
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def embed_with_metadata(self, text: str) -> dict[str, Any]:
        """生成向量并返回元数据

        Args:
            text: 输入文本

        Returns:
            包含向量和元数据的字典
        """
        vector = self.embed(text)
        return {
            "text": text,
            "vector": vector,
            "dimension": len(vector),
            "model": self.model_name,
        }


def demo() -> None:
    """演示 Embedding 功能"""
    print("=" * 50)
    print("Embedding 生成示例")
    print("=" * 50)

    demo = EmbeddingDemo()

    texts = [
        "Python 是一种编程语言",
        "Java 是一种编程语言",
        "今天天气很好",
    ]

    print(f"\n模型: {demo.model_name}")
    print(f"维度: {demo.dimension}")

    # 生成向量
    vectors = demo.embed_batch(texts)

    print(f"\n生成了 {len(vectors)} 个向量:")
    for i, (text, vec) in enumerate(zip(texts, vectors)):
        print(f"\n文本 {i + 1}: {text}")
        print(f"向量维度: {len(vec)}")
        print(f"向量前5个值: {vec[:5]}")

    # 计算相似度
    print("\n" + "-" * 50)
    print("\n相似度计算:")
    sim_01 = demo.similarity(vectors[0], vectors[1])
    sim_02 = demo.similarity(vectors[0], vectors[2])
    print(f"'{texts[0]}' vs '{texts[1]}': {sim_01:.4f}")
    print(f"'{texts[0]}' vs '{texts[2]}': {sim_02:.4f}")


if __name__ == "__main__":
    demo()
