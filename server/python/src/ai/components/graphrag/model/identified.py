"""包含 'Identified' 协议的包。

A package containing the 'Identified' protocol.
"""

from dataclasses import dataclass


@dataclass
class Identified:
    """
    具有唯一标识符的项的协议。

    A protocol for an item with an ID.
    """

    id: str
    """项的唯一标识符。

    The ID of the item.
    """

    short_id: str | None
    """人类可读的短ID,用于在提示词或显示给用户的文本中引用此项(如在报告文本中)(可选)。

    Human readable ID used to refer to this community in prompts or texts displayed to users,
    such as in a report text (optional).
    """
