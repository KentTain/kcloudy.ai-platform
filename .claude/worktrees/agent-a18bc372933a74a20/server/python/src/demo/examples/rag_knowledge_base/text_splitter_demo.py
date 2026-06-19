"""
文档分段示例

演示如何对文本进行分段优化，支持：
- 按章节标题分段
- 按固定长度分段
- 智能句子边界分割

示例使用：
    splitter = ChapterTextSplitter(chunk_size=500)
    chunks = splitter.split(text)
"""

import re
from typing import Any


class TextSplitterDemo:
    """文本分段演示基类"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        """初始化分段器

        Args:
            chunk_size: 每段最大字符数
            chunk_overlap: 相邻段落的重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        """分割文本

        Args:
            text: 待分割的文本

        Returns:
            分段后的文本列表
        """
        raise NotImplementedError


class CharacterTextSplitter(TextSplitterDemo):
    """按字符数分割文本"""

    def split(self, text: str) -> list[str]:
        """按固定字符数分割

        Args:
            text: 待分割的文本

        Returns:
            分段后的文本列表
        """
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks


class SentenceTextSplitter(TextSplitterDemo):
    """按句子边界分割文本"""

    # 中英文句子分隔符
    SENTENCE_PATTERN = re.compile(
        r"(?<=[。！？.!?])\s*"  # 句子结束符后跟空白
    )

    def split(self, text: str) -> list[str]:
        """在句子边界处分割

        Args:
            text: 待分割的文本

        Returns:
            分段后的文本列表
        """
        sentences = self.SENTENCE_PATTERN.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_length + sentence_len > self.chunk_size and current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_len
            else:
                current_chunk.append(sentence)
                current_length += sentence_len

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks


class ChapterTextSplitter(TextSplitterDemo):
    """按章节标题分割文本"""

    # 章节标题匹配模式
    CHAPTER_PATTERNS = [
        re.compile(r"^第[一二三四五六七八九十\d]+章\s+.+$", re.MULTILINE),
        re.compile(r"^Chapter\s+\d+.*$", re.MULTILINE),
        re.compile(r"^#\s+.+$", re.MULTILINE),  # Markdown 标题
    ]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        chapter_patterns: list[re.Pattern[str]] | None = None,
    ) -> None:
        """初始化章节分段器

        Args:
            chunk_size: 每段最大字符数
            chunk_overlap: 相邻段落的重叠字符数
            chapter_patterns: 自定义章节匹配模式
        """
        super().__init__(chunk_size, chunk_overlap)
        self.patterns = chapter_patterns or self.CHAPTER_PATTERNS

    def split(self, text: str) -> list[str]:
        """按章节分割文本

        Args:
            text: 待分割的文本

        Returns:
            分段后的文本列表
        """
        # 查找所有章节边界
        boundaries: list[int] = [0]
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                boundaries.append(match.start())

        # 去重并排序
        boundaries = sorted(set(boundaries))
        boundaries.append(len(text))

        # 按章节分割
        chunks: list[str] = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            section = text[start:end].strip()

            if not section:
                continue

            # 如果章节过长，使用句子分段器进一步分割
            if len(section) > self.chunk_size:
                sentence_splitter = SentenceTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
                chunks.extend(sentence_splitter.split(section))
            else:
                chunks.append(section)

        return chunks

    def split_with_metadata(self, text: str) -> list[dict[str, Any]]:
        """按章节分割文本，返回带元数据的段落

        Args:
            text: 待分割的文本

        Returns:
            包含文本和元数据的字典列表
        """
        chunks = self.split(text)
        return [
            {
                "content": chunk,
                "index": i,
                "length": len(chunk),
            }
            for i, chunk in enumerate(chunks)
        ]


def demo() -> None:
    """演示文本分段功能"""
    print("=" * 50)
    print("文本分段示例")
    print("=" * 50)

    sample_text = """
第1章 Python 简介

Python 是一种解释型、面向对象的编程语言。
它具有简洁的语法和强大的功能。

第2章 变量与数据类型

Python 支持多种数据类型，包括整数、浮点数、字符串等。
变量不需要声明类型，Python 会自动推断。

第3章 函数定义

函数使用 def 关键字定义。
语法格式为：def 函数名(参数):
"""

    print("原始文本:")
    print(sample_text)
    print("\n" + "-" * 50)

    # 章节分割
    splitter = ChapterTextSplitter(chunk_size=100)
    chunks = splitter.split(sample_text)

    print(f"\n章节分割结果 ({len(chunks)} 个段落):")
    for i, chunk in enumerate(chunks):
        print(f"\n段落 {i + 1} (长度: {len(chunk)}):")
        print(chunk[:80] + "..." if len(chunk) > 80 else chunk)


if __name__ == "__main__":
    demo()
