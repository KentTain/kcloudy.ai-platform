"""包含'PipelineWorkflowReference'模型的模块."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

PipelineWorkflowStep = dict[str, Any]
"""表示工作流中的一个步骤."""

PipelineWorkflowConfig = dict[str, Any]
"""表示工作流的配置."""


class PipelineWorkflowReference(BaseModel):
    """表示对工作流的引用,并且可以选择性地作为工作流本身."""

    name: str | None = pydantic_Field(description="Name of the workflow.", default=None)
    """工作流的名称."""

    steps: list[PipelineWorkflowStep] | None = pydantic_Field(
        description="The optional steps for the workflow.", default=None
    )
    """工作流的可选步骤."""

    config: PipelineWorkflowConfig | None = pydantic_Field(
        description="The optional configuration for the workflow.", default=None
    )
    """工作流的可选配置."""
