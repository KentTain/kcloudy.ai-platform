# src/extended/langchain/callbacks/processors/file_processor.py
import uuid
from typing import AsyncGenerator
from loguru import logger
from extended.langchain.callbacks.processors.base import UIPartProcessor, ProcessContext
from ai.controllers.v1.chat.event_types import EventType

_logger = logger.bind(name=__name__)

class FileProcessor(UIPartProcessor):
    """文件附件处理器"""

    FILE_TOOL_KEYWORDS = frozenset([
        "document", "file", "upload", "attachment",
        "pdf", "image", "excel", "word"
    ])

    @classmethod
    def supported_types(cls) -> list[str]:
        return ["file"]

    async def process(self, context: ProcessContext) -> AsyncGenerator[dict, None]:
        """处理工具调用结果，提取文件信息"""
        if not context.tool_name or not context.tool_result:
            return

        if not self._is_file_tool(context.tool_name):
            return

        files = self._extract_files(context.tool_result)

        for file_info in files:
            file_id = f"file-{uuid.uuid4().hex[:8]}"

            try:
                yield {
                    "type": EventType.FILE_UPLOAD_START,
                    "fileId": file_id,
                }

                yield {
                    "type": EventType.FILE_UPLOAD_END,
                    "fileId": file_id,
                    "mediaType": file_info["media_type"],
                    "url": file_info["url"],
                    "filename": file_info.get("filename"),
                    "size": file_info.get("size"),
                }
            except Exception as e:
                _logger.warning(f"Failed to create file event: {e}")

    def _is_file_tool(self, tool_name: str) -> bool:
        """判断是否是文件类工具"""
        if not tool_name:
            return False
        tool_name_lower = tool_name.lower()
        return any(keyword in tool_name_lower for keyword in self.FILE_TOOL_KEYWORDS)

    def _extract_files(self, tool_result) -> list[dict]:
        """从工具结果中提取文件信息"""
        files = []

        if isinstance(tool_result, dict):
            if "files" in tool_result and isinstance(tool_result["files"], list):
                for item in tool_result["files"]:
                    if item.get("url") and item.get("media_type"):
                        files.append({
                            "media_type": item["media_type"],
                            "url": item["url"],
                            "filename": item.get("filename"),
                            "size": item.get("size"),
                        })

            elif "file" in tool_result and isinstance(tool_result["file"], dict):
                item = tool_result["file"]
                if item.get("url") and item.get("media_type"):
                    files.append({
                        "media_type": item["media_type"],
                        "url": item["url"],
                        "filename": item.get("filename"),
                        "size": item.get("size"),
                    })

        return files
