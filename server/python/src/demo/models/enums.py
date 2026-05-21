"""
枚举基类和通用枚举定义
"""

from enum import Enum
from typing_extensions import Self

from demo.utils.enum_util import EnumMemberData


class EnumBase(Enum):
    """枚举基类，提供通用的枚举功能"""

    @classmethod
    def get_enum_list(cls) -> list[EnumMemberData]:
        """获取枚举成员列表

        :return: 枚举成员数据列表
        """
        return [
            EnumMemberData(name=member.name, value=member.value, label=member.label)
            for member in cls
        ]

    @property
    def label(self) -> str:
        """获取枚举成员的显示标签

        默认返回 name，子类可覆盖
        """
        return self.name


class Status(str, EnumBase):
    """通用状态枚举"""

    DISABLE = "0"
    ENABLE = "1"

    @property
    def label(self) -> str:
        labels = {
            Status.DISABLE: "禁用",
            Status.ENABLE: "启用",
        }
        return labels.get(self, self.name)
