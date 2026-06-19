"""
枚举定义
"""

from framework.common.enums import EnumBase


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
