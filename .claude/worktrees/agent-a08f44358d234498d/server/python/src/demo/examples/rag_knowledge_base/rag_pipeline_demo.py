"""
完整 RAG 流程示例

演示 RAG（检索增强生成）的完整流程：
- 文档加载
- 文档分段
- Embedding 生成
- 向量存储
- 检索与回答生成

示例使用：
    rag = SimpleRAGPipeline()
    rag.add_document("example.pdf")
    answer = rag.query("什么是 Python?")
"""

from pathlib import Path
from typing import Any

from demo.examples.rag_knowledge_base.embedding_demo import EmbeddingDemo
from demo.examples.rag_knowledge_base.pdf_parser_demo import PDFParserDemo
from demo.examples.rag_knowledge_base.text_splitter_demo import (
    ChapterTextSplitter,
    TextSplitterDemo,
)
from demo.examples.rag_knowledge_base.vector_store_demo import InMemoryVectorStore


class SimpleRAGPipeline:
    """简单 RAG 管道

    演示完整的 RAG 流程：
    1. 文档加载与分段
    2. Embedding 生成与存储
    3. 检索与上下文构建
    """

    def __init__(
        self,
        chunk_size: int = 500,
        top_k: int = 3,
        threshold: float = 0.3,
    ) -> None:
        """初始化 RAG 管道

        Args:
            chunk_size: 文档分段大小
            top_k: 检索返回的文档数量
            threshold: 相似度阈值
        """
        self.chunk_size = chunk_size
        self.top_k = top_k
        self.threshold = threshold

        # 初始化组件
        self.parser = PDFParserDemo()
        self.splitter = ChapterTextSplitter(chunk_size=chunk_size)
        self.embedding = EmbeddingDemo()
        self.store = InMemoryVectorStore()

        # 存储原始文本
        self._chunks: list[str] = []

    def add_text(self, text: str) -> int:
        """添加文本到知识库

        Args:
            text: 文本内容

        Returns:
            添加的段落数量
        """
        # 分段
        chunks = self.splitter.split(text)
        if not chunks:
            return 0

        # 生成向量
        vectors = self.embedding.embed_batch(chunks)

        # 存储
        self.store.add(chunks, vectors)
        self._chunks.extend(chunks)

        return len(chunks)

    def add_document(self, file_path: str | Path) -> int:
        """添加文档到知识库

        Args:
            file_path: 文档路径

        Returns:
            添加的段落数量
        """
        # 解析文档
        pages = self.parser.parse(file_path)
        full_text = "\n\n".join(pages)

        # 添加文本
        return self.add_text(full_text)

    def query(self, question: str) -> dict[str, Any]:
        """查询知识库

        Args:
            question: 用户问题

        Returns:
            包含答案和上下文的字典
        """
        # 生成查询向量
        query_vector = self.embedding.embed(question)

        # 检索相关文档
        results = self.store.search(
            query_vector,
            top_k=self.top_k,
            threshold=self.threshold,
        )

        # 构建上下文
        contexts = [r["text"] for r in results]
        context = "\n\n---\n\n".join(contexts)

        return {
            "question": question,
            "contexts": contexts,
            "context": context,
            "scores": [r["score"] for r in results],
            "has_results": len(results) > 0,
        }

    def count_documents(self) -> int:
        """返回知识库中的段落数量"""
        return self.store.count()


class RAGPipelineDemo:
    """RAG 管道演示类

    演示完整的 RAG 工作流程
    """

    def __init__(self) -> None:
        """初始化演示"""
        self.pipeline = SimpleRAGPipeline()

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("RAG 流程演示")
        print("=" * 50)

        # 添加示例文档
        sample_docs = [
            """
第1章 Python 简介

Python 是一种解释型、面向对象的编程语言。它的设计哲学强调代码的可读性和简洁性。
Python 支持多种编程范式，包括面向对象、命令式、函数式编程。

第2章 变量与数据类型

Python 支持多种内置数据类型：整数(int)、浮点数(float)、字符串(str)、列表(list)、
字典(dict)等。变量不需要声明类型，Python 解释器会自动推断。

第3章 函数定义

Python 使用 def 关键字定义函数。语法格式为：
def 函数名(参数):
    函数体
    return 返回值

函数可以有默认参数、可变参数和关键字参数。
            """,
            """
第4章 类与对象

Python 是面向对象的语言。使用 class 关键字定义类：
class ClassName:
    def __init__(self):
        pass

类可以继承、多态和封装。

第5章 模块与包

Python 使用 import 导入模块。模块是包含 Python 代码的 .py 文件。
包是包含 __init__.py 的目录，用于组织模块。
            """,
        ]

        print("\n1. 添加文档到知识库...")
        total_chunks = 0
        for i, doc in enumerate(sample_docs):
            chunks = self.pipeline.add_text(doc)
            total_chunks += chunks
            print(f"   文档 {i + 1}: 添加了 {chunks} 个段落")

        print(f"\n   总计: {total_chunks} 个段落")

        # 查询演示
        questions = [
            "Python 如何定义函数？",
            "Python 支持哪些数据类型？",
            "什么是面向对象编程？",
        ]

        print("\n2. 查询演示...")
        for question in questions:
            print(f"\n问题: {question}")
            result = self.pipeline.query(question)

            if result["has_results"]:
                print(f"找到 {len(result['contexts'])} 个相关段落:")
                for i, (ctx, score) in enumerate(
                    zip(result["contexts"], result["scores"])
                ):
                    print(f"   [{i + 1}] 相似度: {score:.4f}")
                    print(f"       {ctx[:60]}...")
            else:
                print("   未找到相关内容")


def demo() -> None:
    """演示 RAG 流程"""
    demo_instance = RAGPipelineDemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
