"""包含'PipelineRunResult'模型的模块."""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

ErrorHandlerFn = Callable[[BaseException | None, str | None, dict | None], None]


@dataclass
class PipelineRunResult:
    """流水线运行结果类定义."""

    workflow: str
    result: pd.DataFrame | None
    errors: list[BaseException] | None
