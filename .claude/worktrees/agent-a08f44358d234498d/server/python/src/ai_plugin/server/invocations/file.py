from enum import Enum

import requests
from pydantic import BaseModel, model_validator

from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class UploadFileResponse(BaseModel):
    """
    文件上传响应模型类

    封装文件上传后的响应信息
    """

    class Type(str, Enum):
        """
        文件类型枚举

        根据MIME类型判断文件的分类
        """

        DOCUMENT = "document"  # 文档类型
        IMAGE = "image"  # 图像类型
        VIDEO = "video"  # 视频类型
        AUDIO = "audio"  # 音频类型

        @classmethod
        def from_mime_type(cls, mime_type: str):
            """
            根据MIME类型判断文件类型

            Args:
                mime_type: MIME类型字符串

            Returns:
                Type: 对应的文件类型枚举
            """
            if mime_type.startswith("image/"):
                return cls.IMAGE
            if mime_type.startswith("video/"):
                return cls.VIDEO
            if mime_type.startswith("audio/"):
                return cls.AUDIO

            return cls.DOCUMENT

    id: str  # 文件ID
    name: str  # 文件名
    size: int  # 文件大小（字节）
    extension: str  # 文件扩展名
    mime_type: str  # MIME类型
    type: Type | None = None  # 文件类型（可选）
    preview_url: str | None = None  # 预览URL（可选）

    @model_validator(mode="before")
    @classmethod
    def validate_type(cls, d):
        """
        验证文件类型

        如果未指定类型，则根据MIME类型自动判断
        """
        if "type" not in d:
            d["type"] = cls.Type.from_mime_type(d.get("mime_type", ""))
        return d

    def to_app_parameter(self) -> dict:
        """
        转换为应用参数格式

        Returns:
            dict: 应用可使用的参数字典
        """
        return {
            "upload_file_id": self.id,
            "transfer_method": "local_file",
            "type": self.Type.from_mime_type(self.mime_type).value,
        }


class File(BackwardsInvocation[dict]):
    """
    文件操作类

    提供文件上传等文件相关操作的接口
    """

    def upload(
        self, filename: str, content: bytes, mimetype: str
    ) -> UploadFileResponse:
        """
        上传文件

        Args:
            filename: 文件名
            content: 文件内容（字节数据）
            mimetype: 文件MIME类型

        Returns:
            UploadFileResponse: 上传响应信息

        Raises:
            Exception: 当上传失败时抛出异常
        """
        for response in self._backwards_invoke(
            InvokeType.UploadFile,
            dict,
            {
                "filename": filename,
                "mimetype": mimetype,
            },
        ):
            url = response.get("url")
            if not url:
                raise Exception("上传文件失败，无法获取签名URL")

            response = requests.post(url, files={"file": (filename, content, mimetype)})
            if response.status_code != 201:
                raise Exception(
                    f"上传文件失败，状态码: {response.status_code}，响应: {response.text}"
                )

            return UploadFileResponse(**response.json())

        raise Exception("上传文件失败，服务器返回空响应")
