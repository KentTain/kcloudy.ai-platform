"""
PDF 解析示例

演示如何使用 PyPDF 解析 PDF 文件，提取纯文本内容。
支持去除页眉页脚，按页返回文本列表。

示例使用：
    parser = PDFParserDemo()
    pages = parser.parse("example.pdf")
    for i, page in enumerate(pages):
        print(f"Page {i+1}: {page[:100]}...")
"""

from pathlib import Path
from typing import Any

from pypdf import PdfReader


class PDFParserDemo:
    """PDF 文档解析演示类

    演示功能：
    - 解析 PDF 文件提取文本
    - 去除页眉页脚
    - 按页返回文本列表
    """

    def __init__(
        self,
        header_text: str | None = None,
        footer_text: str | None = None,
    ) -> None:
        """初始化 PDF 解析器

        Args:
            header_text: 需要去除的页眉文本
            footer_text: 需要去除的页脚文本
        """
        self.header_text = header_text
        self.footer_text = footer_text

    def parse(self, file_path: str | Path) -> list[str]:
        """解析 PDF 文件，提取文本内容

        Args:
            file_path: PDF 文件路径

        Returns:
            按页分割的文本列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件不是 PDF 格式
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {file_path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"文件不是 PDF 格式: {file_path}")

        text_list: list[str] = []
        reader = PdfReader(str(path))

        for page in reader.pages:
            text = page.extract_text() or ""
            text = self._clean_text(text)
            text_list.append(text)

        return text_list

    def _clean_text(self, text: str) -> str:
        """清理文本，去除页眉页脚

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if self.header_text:
            text = text.replace(self.header_text, "")
        if self.footer_text:
            text = text.replace(self.footer_text, "")
        return text.strip()

    def parse_with_metadata(self, file_path: str | Path) -> dict[str, Any]:
        """解析 PDF 文件，返回文本和元数据

        Args:
            file_path: PDF 文件路径

        Returns:
            包含文本和元数据的字典
        """
        path = Path(file_path)
        reader = PdfReader(str(path))

        pages = self.parse(file_path)
        metadata = reader.metadata or {}

        return {
            "pages": pages,
            "page_count": len(pages),
            "metadata": {
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
            },
        }


def parse_pdf_file(
    file_path: str | Path,
    header_text: str | None = None,
    footer_text: str | None = None,
) -> list[str]:
    """便捷函数：解析 PDF 文件

    Args:
        file_path: PDF 文件路径
        header_text: 需要去除的页眉文本
        footer_text: 需要去除的页脚文本

    Returns:
        按页分割的文本列表
    """
    parser = PDFParserDemo(header_text=header_text, footer_text=footer_text)
    return parser.parse(file_path)


def demo() -> None:
    """演示 PDF 解析功能"""
    print("=" * 50)
    print("PDF 解析示例")
    print("=" * 50)

    # 示例：创建一个简单的测试
    parser = PDFParserDemo(header_text="页眉：Python手册")
    print("PDF 解析器已初始化")
    print(f"页眉过滤: '{parser.header_text}'")
    print("\n使用方法:")
    print("  pages = parser.parse('example.pdf')")
    print("  for i, page in enumerate(pages):")
    print("      print(f'Page {i+1}: {page[:100]}...')")


if __name__ == "__main__":
    demo()
