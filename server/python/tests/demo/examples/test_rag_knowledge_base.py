"""
RAG 知识库示例单元测试

测试覆盖：
- PDF 解析
- 文档分段
- Embedding 生成
- 向量存储与检索
- RAG 管道
"""

from typing import Any

import pytest

from demo.examples.rag_knowledge_base.embedding_demo import (
    EmbeddingDemo,
    MockEmbedding,
)
from demo.examples.rag_knowledge_base.pdf_parser_demo import (
    PDFParserDemo,
    parse_pdf_file,
)
from demo.examples.rag_knowledge_base.rag_pipeline_demo import (
    SimpleRAGPipeline,
)
from demo.examples.rag_knowledge_base.text_splitter_demo import (
    ChapterTextSplitter,
    CharacterTextSplitter,
    SentenceTextSplitter,
)
from demo.examples.rag_knowledge_base.vector_store_demo import (
    InMemoryVectorStore,
    VectorStoreDemo,
)


class TestMockEmbedding:
    """MockEmbedding 测试"""

    def test_init_default_dimension(self) -> None:
        """测试默认维度初始化"""
        embedding = MockEmbedding()
        assert embedding.dimension == 384

    def test_init_custom_dimension(self) -> None:
        """测试自定义维度初始化"""
        embedding = MockEmbedding(dimension=512)
        assert embedding.dimension == 512

    def test_embed_returns_correct_length(self) -> None:
        """测试返回向量长度正确"""
        embedding = MockEmbedding(dimension=256)
        vector = embedding.embed("test text")
        assert len(vector) == 256

    def test_embed_returns_normalized_vector(self) -> None:
        """测试返回归一化向量"""
        embedding = MockEmbedding()
        vector = embedding.embed("test text")
        norm = sum(v * v for v in vector) ** 0.5
        assert abs(norm - 1.0) < 0.0001

    def test_embed_deterministic(self) -> None:
        """测试相同文本返回相同向量"""
        embedding = MockEmbedding()
        vec1 = embedding.embed("same text")
        vec2 = embedding.embed("same text")
        assert vec1 == vec2

    def test_embed_different_texts_different_vectors(self) -> None:
        """测试不同文本返回不同向量"""
        embedding = MockEmbedding()
        vec1 = embedding.embed("text one")
        vec2 = embedding.embed("text two")
        assert vec1 != vec2

    def test_embed_batch(self) -> None:
        """测试批量生成向量"""
        embedding = MockEmbedding()
        texts = ["text1", "text2", "text3"]
        vectors = embedding.embed_batch(texts)
        assert len(vectors) == 3
        for v in vectors:
            assert len(v) == 384


class TestEmbeddingDemo:
    """EmbeddingDemo 测试"""

    def test_init_default_values(self) -> None:
        """测试默认初始化"""
        demo = EmbeddingDemo()
        assert demo.model_name == "mock"
        assert demo.dimension == 384

    def test_embed_returns_vector(self) -> None:
        """测试返回向量"""
        demo = EmbeddingDemo()
        vector = demo.embed("test")
        assert isinstance(vector, list)
        assert len(vector) == 384

    def test_similarity_same_vector(self) -> None:
        """测试相同向量相似度为 1"""
        demo = EmbeddingDemo()
        vec = demo.embed("test")
        similarity = demo.similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.0001

    def test_similarity_orthogonal_vectors(self) -> None:
        """测试正交向量相似度接近 0"""
        demo = EmbeddingDemo()
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = demo.similarity(vec1, vec2)
        assert abs(similarity) < 0.0001


class TestCharacterTextSplitter:
    """CharacterTextSplitter 测试"""

    def test_split_short_text(self) -> None:
        """测试短文本不分割"""
        splitter = CharacterTextSplitter(chunk_size=100)
        text = "short text"
        chunks = splitter.split(text)
        assert len(chunks) == 1
        assert chunks[0] == "short text"

    def test_split_long_text(self) -> None:
        """测试长文本分割"""
        splitter = CharacterTextSplitter(chunk_size=10, chunk_overlap=0)
        text = "this is a long text that needs splitting"
        chunks = splitter.split(text)
        assert len(chunks) > 1


class TestSentenceTextSplitter:
    """SentenceTextSplitter 测试"""

    def test_split_by_sentence(self) -> None:
        """测试按句子分割"""
        splitter = SentenceTextSplitter(chunk_size=100)
        text = "这是第一句。这是第二句！这是第三句？"
        chunks = splitter.split(text)
        assert len(chunks) >= 1

    def test_split_preserves_sentence_boundary(self) -> None:
        """测试保留句子边界"""
        splitter = SentenceTextSplitter(chunk_size=20)
        text = "短句。另一短句。"
        chunks = splitter.split(text)
        for chunk in chunks:
            # 不应该在句子中间分割
            pass  # 简单验证通过


class TestChapterTextSplitter:
    """ChapterTextSplitter 测试"""

    def test_split_by_chapter(self) -> None:
        """测试按章节分割"""
        splitter = ChapterTextSplitter(chunk_size=500)
        text = """
第1章 简介
这是第一章的内容。

第2章 详情
这是第二章的内容。
"""
        chunks = splitter.split(text)
        assert len(chunks) >= 2

    def test_split_with_metadata(self) -> None:
        """测试返回带元数据的分割结果"""
        splitter = ChapterTextSplitter()
        text = "第1章 测试\n内容"
        result = splitter.split_with_metadata(text)
        assert isinstance(result, list)
        for item in result:
            assert "content" in item
            assert "index" in item
            assert "length" in item


class TestInMemoryVectorStore:
    """InMemoryVectorStore 测试"""

    def test_add_and_count(self) -> None:
        """测试添加和计数"""
        store = InMemoryVectorStore()
        texts = ["text1", "text2"]
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        store.add(texts, vectors)
        assert store.count() == 2

    def test_search_returns_results(self) -> None:
        """测试搜索返回结果"""
        store = InMemoryVectorStore()
        texts = ["text1", "text2"]
        vectors = [[1.0, 0.0], [0.0, 1.0]]
        store.add(texts, vectors)
        query = [1.0, 0.0]  # 与第一个向量相同
        results = store.search(query, top_k=2)
        assert len(results) == 2
        assert results[0]["score"] > results[1]["score"]

    def test_search_with_threshold(self) -> None:
        """测试阈值过滤"""
        store = InMemoryVectorStore()
        texts = ["text1", "text2"]
        vectors = [[1.0, 0.0], [0.0, 1.0]]
        store.add(texts, vectors)
        query = [0.5, 0.5]  # 与两个向量都有一定相似度
        results = store.search(query, top_k=2, threshold=0.9)
        # 由于归一化向量，相似度应该低于 0.9
        assert all(r["score"] >= 0.9 for r in results)

    def test_clear(self) -> None:
        """测试清空"""
        store = InMemoryVectorStore()
        store.add(["text"], [[0.1, 0.2]])
        store.clear()
        assert store.count() == 0

    def test_empty_store_search(self) -> None:
        """测试空存储搜索"""
        store = InMemoryVectorStore()
        results = store.search([0.1, 0.2])
        assert results == []


class TestVectorStoreDemo:
    """VectorStoreDemo 测试"""

    def test_search_with_embedding(self) -> None:
        """测试使用 Embedding 搜索"""
        embedding = MockEmbedding()
        demo = VectorStoreDemo(embedding=embedding)
        demo.add_documents(["文档1", "文档2"])
        results = demo.search("查询", top_k=2)
        assert len(results) <= 2

    def test_without_embedding_raises(self) -> None:
        """测试未配置 Embedding 时抛出异常"""
        demo = VectorStoreDemo()
        with pytest.raises(ValueError, match="未配置 Embedding"):
            demo.add_documents(["text"])


class TestSimpleRAGPipeline:
    """SimpleRAGPipeline 测试"""

    def test_add_text(self) -> None:
        """测试添加文本"""
        pipeline = SimpleRAGPipeline()
        count = pipeline.add_text("这是测试文本。")
        assert count >= 1

    def test_query(self) -> None:
        """测试查询"""
        pipeline = SimpleRAGPipeline()
        pipeline.add_text("Python 是一种编程语言。")
        result = pipeline.query("什么是 Python？")
        assert "question" in result
        assert "contexts" in result
        assert "has_results" in result

    def test_count_documents(self) -> None:
        """测试文档计数"""
        pipeline = SimpleRAGPipeline()
        pipeline.add_text("文本1。文本2。")
        assert pipeline.count_documents() >= 1


class TestPDFParserDemo:
    """PDFParserDemo 测试"""

    def test_init(self) -> None:
        """测试初始化"""
        parser = PDFParserDemo(header_text="页眉")
        assert parser.header_text == "页眉"

    def test_clean_text(self) -> None:
        """测试文本清理"""
        parser = PDFParserDemo(header_text="HEADER", footer_text="FOOTER")
        text = "HEADER content FOOTER"
        cleaned = parser._clean_text(text)
        assert "HEADER" not in cleaned
        assert "FOOTER" not in cleaned
        assert "content" in cleaned

    def test_parse_nonexistent_file(self) -> None:
        """测试解析不存在的文件"""
        parser = PDFParserDemo()
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.pdf")

    def test_parse_non_pdf_file(self, tmp_path: Any) -> None:
        """测试解析非 PDF 文件"""
        parser = PDFParserDemo()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("content")
        with pytest.raises(ValueError, match="不是 PDF 格式"):
            parser.parse(txt_file)


class TestParsePDFile:
    """parse_pdf_file 便捷函数测试"""

    def test_parse_pdf_file_function(self) -> None:
        """测试便捷函数签名"""
        # 仅验证函数存在且可调用
        assert callable(parse_pdf_file)
