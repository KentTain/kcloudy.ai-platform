"""
向量存储与检索示例

演示如何使用内存向量库进行：
- 向量存储与索引
- 相似度检索
- 阈值过滤

示例使用：
    store = InMemoryVectorStore()
    store.add(["text1", "text2"], vectors)
    results = store.search(query_vector, top_k=5)
"""

from typing import Any


class InMemoryVectorStore:
    """内存向量存储

    演示功能：
    - 添加向量和文档
    - 相似度检索
    - 阈值过滤
    """

    def __init__(self) -> None:
        """初始化向量存储"""
        self._documents: list[dict[str, Any]] = []
        self._vectors: list[list[float]] = []

    def add(
        self,
        texts: list[str],
        vectors: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """添加文档和向量

        Args:
            texts: 文本列表
            vectors: 向量列表
            metadatas: 元数据列表（可选）
        """
        if len(texts) != len(vectors):
            raise ValueError("文本数量与向量数量不匹配")

        for i, (text, vector) in enumerate(zip(texts, vectors)):
            doc: dict[str, Any] = {
                "id": len(self._documents),
                "text": text,
                "metadata": metadatas[i] if metadatas else {},
            }
            self._documents.append(doc)
            self._vectors.append(vector)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """相似度检索

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            threshold: 相似度阈值

        Returns:
            检索结果列表
        """
        if not self._vectors:
            return []

        # 计算相似度
        scores: list[tuple[int, float]] = []
        for i, vec in enumerate(self._vectors):
            score = self._cosine_similarity(query_vector, vec)
            if score >= threshold:
                scores.append((i, score))

        # 按相似度排序
        scores.sort(key=lambda x: x[1], reverse=True)

        # 返回 Top-K 结果
        results: list[dict[str, Any]] = []
        for i, (idx, score) in enumerate(scores[:top_k]):
            result = {
                **self._documents[idx],
                "score": score,
                "rank": i + 1,
            }
            results.append(result)

        return results

    def _cosine_similarity(
        self,
        vec1: list[float],
        vec2: list[float],
    ) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def count(self) -> int:
        """返回存储的文档数量"""
        return len(self._documents)

    def clear(self) -> None:
        """清空存储"""
        self._documents.clear()
        self._vectors.clear()

    def get_all_documents(self) -> list[dict[str, Any]]:
        """获取所有文档"""
        return self._documents.copy()


class VectorStoreDemo:
    """向量存储演示类

    演示功能：
    - 文档索引
    - 向量检索
    - 结果过滤
    """

    def __init__(self, embedding: Any = None) -> None:
        """初始化演示

        Args:
            embedding: Embedding 实例（可选）
        """
        self.store = InMemoryVectorStore()
        self.embedding = embedding

    def add_documents(self, texts: list[str]) -> None:
        """添加文档

        Args:
            texts: 文本列表
        """
        if self.embedding is None:
            raise ValueError("未配置 Embedding")

        vectors = self.embedding.embed_batch(texts)
        self.store.add(texts, vectors)

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """检索文档

        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值

        Returns:
            检索结果
        """
        if self.embedding is None:
            raise ValueError("未配置 Embedding")

        query_vector = self.embedding.embed(query)
        return self.store.search(query_vector, top_k, threshold)


def demo() -> None:
    """演示向量存储功能"""
    print("=" * 50)
    print("向量存储与检索示例")
    print("=" * 50)

    from demo.examples.rag_knowledge_base.embedding_demo import MockEmbedding

    # 初始化
    embedding = MockEmbedding(dimension=384)
    store = InMemoryVectorStore()

    # 添加文档
    documents = [
        "Python 是一种解释型编程语言",
        "Java 是一种面向对象编程语言",
        "JavaScript 用于网页开发",
        "Go 语言由 Google 开发",
        "Rust 注重安全和性能",
    ]

    vectors = embedding.embed_batch(documents)
    store.add(documents, vectors)

    print(f"\n已添加 {store.count()} 个文档")

    # 检索
    query = "什么是编程语言"
    query_vector = embedding.embed(query)

    print(f"\n查询: {query}")
    print("-" * 30)

    results = store.search(query_vector, top_k=3)
    for result in results:
        print(f"\n排名 {result['rank']}: {result['text']}")
        print(f"相似度: {result['score']:.4f}")

    # 阈值过滤演示
    print("\n" + "=" * 50)
    print("阈值过滤演示 (threshold=0.5)")
    results = store.search(query_vector, top_k=5, threshold=0.5)
    print(f"过滤后结果数: {len(results)}")


if __name__ == "__main__":
    demo()
