"""包含 'Named' 协议的包。

A package containing the 'Named' protocol.
"""

from dataclasses import dataclass

from ai.components.graphrag.model.identified import Identified


@dataclass
class Named(Identified):
    """
    具有名称/标题的项的协议。

    继承自 Identified,在 ID 的基础上增加了标题属性。

    A protocol for an item with a name/title.
    """

    title: str
    """项的名称/标题。

    The name/title of the item.
    """
