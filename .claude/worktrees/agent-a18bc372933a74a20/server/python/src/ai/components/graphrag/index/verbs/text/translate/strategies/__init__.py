"""初始化组件图谱检索增强生成包。"""

from ai.components.graphrag.index.verbs.text.translate.strategies.mock import (
    run as run_mock,
)
from ai.components.graphrag.index.verbs.text.translate.strategies.openai import (
    run as run_openai,
)

__all__ = ["run_mock", "run_openai"]
