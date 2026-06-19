"""
智能体知识库关联示例

演示智能体如何关联知识库：
- 知识库检索
- 检索结果整合
- 回退策略

示例使用：
    kb = AgentKnowledgeBase()
    result = kb.retrieve("什么是 Python?")
"""

from typing import Any


class MockRetriever:
    """Mock 检索器，用于测试

    提供简单的关键词匹配检索功能。
    """

    def __init__(self) -> None:
        """初始化检索器"""
        self._documents: list[dict[str, Any]] = []

    def add_document(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """添加文档

        Args:
            content: 文档内容
            metadata: 元数据
        """
        self._documents.append(
            {
                "content": content,
                "metadata": metadata or {},
            }
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """检索文档

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        results: list[dict[str, Any]] = []

        for doc in self._documents:
            # 简单关键词匹配
            keywords = query.lower().split()
            content_lower = doc["content"].lower()
            score = sum(1 for kw in keywords if kw in content_lower) / len(keywords)

            if score > 0:
                results.append(
                    {
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "score": score,
                    }
                )

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class AgentKnowledgeBase:
    """智能体知识库

    管理知识库检索和结果整合。
    """

    def __init__(
        self,
        retriever: MockRetriever | None = None,
        fallback_to_llm: bool = True,
    ) -> None:
        """初始化知识库

        Args:
            retriever: 检索器实例
            fallback_to_llm: 无结果时是否回退到 LLM
        """
        self.retriever = retriever or MockRetriever()
        self.fallback_to_llm = fallback_to_llm
        self._min_score = 0.1

    def add_documents(self, documents: list[str]) -> None:
        """批量添加文档

        Args:
            documents: 文档内容列表
        """
        for doc in documents:
            self.retriever.add_document(doc)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """检索知识库

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果
        """
        results = self.retriever.retrieve(query, top_k)

        # 过滤低分结果
        filtered = [r for r in results if r["score"] >= self._min_score]

        return {
            "query": query,
            "results": filtered,
            "has_results": len(filtered) > 0,
            "fallback": len(filtered) == 0 and self.fallback_to_llm,
        }

    def get_context(self, query: str, top_k: int = 3) -> str:
        """获取检索上下文

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            拼接的上下文文本
        """
        result = self.retrieve(query, top_k)

        if not result["has_results"]:
            return ""

        contexts = [r["content"] for r in result["results"]]
        return "\n\n---\n\n".join(contexts)

    def build_prompt_with_context(
        self,
        query: str,
        system_prompt: str = "",
    ) -> str:
        """构建带上下文的提示词

        Args:
            query: 查询文本
            system_prompt: 系统提示词

        Returns:
            完整提示词
        """
        context = self.get_context(query)

        if context:
            return f"""{system_prompt}

相关上下文：
{context}

用户问题：{query}"""
        elif self.fallback_to_llm:
            return f"""{system_prompt}

用户问题：{query}

注意：知识库中未找到相关内容，请根据通用知识回答。"""
        else:
            return f"""{system_prompt}

用户问题：{query}

抱歉，知识库中没有找到相关内容。"""


class KnowledgeBaseDemo:
    """知识库演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.kb = AgentKnowledgeBase()

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("智能体知识库关联示例")
        print("=" * 50)

        # 添加示例文档
        documents = [
            "Python 是一种解释型、面向对象的编程语言。",
            "Python 使用 def 关键字定义函数。",
            "Python 支持多种数据类型：整数、浮点数、字符串、列表等。",
            "Java 是一种面向对象的编程语言。",
        ]

        print("\n1. 添加文档到知识库...")
        self.kb.add_documents(documents)
        print(f"   已添加 {len(documents)} 个文档")

        # 检索演示
        queries = [
            "什么是 Python？",
            "如何定义函数？",
            "什么是 Java？",
        ]

        print("\n2. 检索演示...")
        for query in queries:
            print(f"\n查询: {query}")
            result = self.kb.retrieve(query)
            if result["has_results"]:
                for r in result["results"]:
                    print(f"   - [{r['score']:.2f}] {r['content'][:50]}...")
            else:
                print("   未找到相关内容，将回退到 LLM")

        # 构建提示词
        print("\n" + "-" * 50)
        print("\n3. 构建带上下文的提示词...")
        prompt = self.kb.build_prompt_with_context(
            "Python 支持哪些数据类型？",
            "你是一个 Python 专家。",
        )
        print(prompt[:200] + "...")


def demo() -> None:
    """演示知识库功能"""
    demo_instance = KnowledgeBaseDemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
