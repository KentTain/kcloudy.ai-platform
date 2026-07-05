# tests/extended/langchain/callbacks/parts/test_parts.py
import pytest
from extended.langchain.callbacks.parts.source_part import SourceUrlPart, SourceDocumentPart
from extended.langchain.callbacks.parts.file_part import FilePart
from extended.langchain.callbacks.parts.data_part import DataPart

class TestSourceParts:
    def test_source_url_part_creation(self):
        """测试创建 SourceUrlPart"""
        part = SourceUrlPart(
            url="https://example.com",
            title="Example",
        )

        assert part.type == "source-url"
        assert part.url == "https://example.com"
        assert part.title == "Example"
        assert part.source_id.startswith("source-")

    def test_source_document_part_creation(self):
        """测试创建 SourceDocumentPart"""
        part = SourceDocumentPart(
            media_type="application/pdf",
            url="https://example.com/doc.pdf",
            title="Document",
        )

        assert part.type == "source-document"
        assert part.media_type == "application/pdf"
        assert part.url == "https://example.com/doc.pdf"
        assert part.title == "Document"

class TestFilePart:
    def test_file_part_creation(self):
        """测试创建 FilePart"""
        part = FilePart(
            media_type="application/pdf",
            url="https://minio.example.com/doc.pdf",
            filename="document.pdf",
            size=1048576,
        )

        assert part.type == "file"
        assert part.media_type == "application/pdf"
        assert part.filename == "document.pdf"
        assert part.size == 1048576

class TestDataPart:
    def test_data_part_creation(self):
        """测试创建 DataPart"""
        part = DataPart(
            type="table",
            content={
                "headers": ["Name", "Age"],
                "rows": [["Alice", 25]],
            }
        )

        assert part.type == "table"
        assert part.id.startswith("data-")
        assert part.content["headers"] == ["Name", "Age"]
