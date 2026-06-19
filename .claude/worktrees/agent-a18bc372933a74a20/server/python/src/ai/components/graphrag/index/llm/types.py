"""包含'LLMtype'模型的模块."""

from collections.abc import Callable
from typing import TypeAlias

TextSplitter: TypeAlias = Callable[[str], list[str]]
TextListSplitter: TypeAlias = Callable[[list[str]], list[str]]
