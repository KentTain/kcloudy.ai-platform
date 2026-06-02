import httpx
from pydantic import BaseModel

from ai_plugin.sdk.file.constants import DIFY_FILE_IDENTITY, FILE_MODEL_IDENTITY
from ai_plugin.sdk.file.entities import FileType


class File(BaseModel):
    """
    文件模型类

    表示一个文件对象，包含文件的基本信息和内容获取方法
    """

    dify_model_identity: str = DIFY_FILE_IDENTITY  # Dify文件标识
    model_identity: str = FILE_MODEL_IDENTITY  # 文件模型标识
    url: str  # 文件URL
    mime_type: str | None = None  # MIME类型（可选）
    filename: str | None = None  # 文件名（可选）
    extension: str | None = None  # 文件扩展名（可选）
    size: int | None = None  # 文件大小（可选）
    type: FileType  # 文件类型

    _blob: bytes | None = None  # 私有属性：文件内容缓存

    @property
    def blob(self) -> bytes:
        """
        获取文件内容作为字节对象

        如果文件内容尚未加载，将从URL加载并存储在`_blob`属性中

        Returns:
            bytes: 文件的二进制内容

        Raises:
            ValueError: 如果URL使用不支持的协议（例如，缺少'http://'或'https://'），
                       建议配置FILES_URL环境变量
            httpx.HTTPStatusError: 如果获取文件的请求失败
        """
        if self._blob is None:
            try:
                response = httpx.get(self.url)
                response.raise_for_status()
                self._blob = response.content
            except httpx.UnsupportedProtocol as e:
                raise ValueError(
                    f"无效的文件URL '{self.url}': {e}. 请确保在.env文件中设置了`FILES_URL`环境变量"
                ) from e

        assert self._blob is not None
        return self._blob
