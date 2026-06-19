"""
RAG 知识库示例模块

本模块演示 RAG（检索增强生成）技术的核心组件：
- PDF 文档解析
- 文档分段优化
- Embedding 生成
- 向量存储与检索
- 完整 RAG 流程

示例使用：
    from demo.examples.rag_knowledge_base import PDFParserDemo, TextSplitterDemo
    from demo.examples.rag_knowledge_base import EmbeddingDemo, VectorStoreDemo
"""

from demo.examples.rag_knowledge_base.embedding_demo import (
    EmbeddingDemo,
    MockEmbedding,
)
from demo.examples.rag_knowledge_base.pdf_parser_demo import (
    PDFParserDemo,
    parse_pdf_file,
)
from demo.examples.rag_knowledge_base.rag_pipeline_demo import (
    RAGPipelineDemo,
    SimpleRAGPipeline,
)
from demo.examples.rag_knowledge_base.text_splitter_demo import (
    ChapterTextSplitter,
    TextSplitterDemo,
)
from demo.examples.rag_knowledge_base.vector_store_demo import (
    InMemoryVectorStore,
    VectorStoreDemo,
)

__all__ = [
    "PDFParserDemo",
    "parse_pdf_file",
    "ChapterTextSplitter",
    "TextSplitterDemo",
    "EmbeddingDemo",
    "MockEmbedding",
    "InMemoryVectorStore",
    "VectorStoreDemo",
    "RAGPipelineDemo",
    "SimpleRAGPipeline",
]
