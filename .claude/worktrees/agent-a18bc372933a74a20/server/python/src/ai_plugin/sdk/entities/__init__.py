from typing import Optional

from pydantic import BaseModel

from ai_plugin.server.core.documentation.schema_doc import docs


@docs(
    description="通用国际化对象",
)
class I18nObject(BaseModel):
    """
    国际化对象模型类

    用于处理多语言文本，支持中文简体、葡萄牙语（巴西）和英语
    """

    zh_Hans: str | None = None  # 中文简体
    pt_BR: str | None = None  # 葡萄牙语（巴西）
    en_US: str  # 英语（必填）

    def __init__(self, **data):
        """
        初始化国际化对象

        如果某些语言版本未提供，则使用英语版本作为默认值

        Args:
            **data: 初始化数据
        """
        super().__init__(**data)
        # 如果没有提供中文简体版本，使用英语版本
        if not self.zh_Hans:
            self.zh_Hans = self.en_US
        # 如果没有提供葡萄牙语版本，使用英语版本
        if not self.pt_BR:
            self.pt_BR = self.en_US

    def to_dict(self) -> dict:
        """
        转换为字典格式

        Returns:
            dict: 包含所有语言版本的字典
        """
        return {"zh_Hans": self.zh_Hans, "en_US": self.en_US, "pt_BR": self.pt_BR}

    @property
    def path(self):
        return self.en_US
