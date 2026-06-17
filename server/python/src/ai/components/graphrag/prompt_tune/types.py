"""提示词微调的类型定义。

Types for prompt tuning.
"""

from enum import Enum


class DocSelectionType(Enum):
    """
    文档选择类型枚举。

    定义在提示词微调过程中如何选择文档样本的策略。

    The type of document selection to use.
    """

    ALL = "all"
    """选择所有文档。

    Select all documents.
    """

    RANDOM = "random"
    """随机选择文档。

    Randomly select documents.
    """

    TOP = "top"
    """选择排名靠前的文档。

    Select top-ranked documents.
    """

    AUTO = "auto"
    """自动确定选择方法。

    Automatically determine the selection method.
    """

    def __str__(self):
        """
        返回枚举值的字符串表示。

        Return the string representation of the enum value.
        """
        return self.value
