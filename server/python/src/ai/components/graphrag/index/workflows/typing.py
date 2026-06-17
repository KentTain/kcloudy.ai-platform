"""包含 'WorkflowToRun' 模型的模块."""

from collections.abc import Callable
from dataclasses import dataclass as dc_dataclass
from typing import Any

from datashaper import TableContainer, Workflow

StepDefinition = dict[str, Any]
"""步骤定义."""

VerbDefinitions = dict[str, Callable[..., TableContainer]]
"""verb 名称到其实现的映射."""

WorkflowConfig = dict[str, Any]
"""workflow 配置."""

WorkflowDefinitions = dict[str, Callable[[WorkflowConfig], list[StepDefinition]]]
"""workflow 名称到其实现的映射."""

VerbTiming = dict[str, float]
"""按 id 记录的 verbs 执行时间."""


@dc_dataclass
class WorkflowToRun:
    """要运行的 workflow 类定义."""

    workflow: Workflow
    config: dict[str, Any]
