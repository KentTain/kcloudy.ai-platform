from enum import StrEnum


class FileType(StrEnum):
    """
    文件类型枚举类

    定义支持的各种文件类型
    """

    IMAGE = "image"  # 图像文件
    DOCUMENT = "document"  # 文档文件
    AUDIO = "audio"  # 音频文件
    VIDEO = "video"  # 视频文件
    CUSTOM = "custom"  # 自定义文件

    @staticmethod
    def value_of(value):
        """
        根据值获取对应的文件类型

        Args:
            value: 文件类型值

        Returns:
            FileType: 对应的文件类型枚举

        Raises:
            ValueError: 当文件类型值无效时抛出
        """
        for member in FileType:
            if member.value == value:
                return member
        raise ValueError(f"不存在此文件类型: {value}")
