"""包含'PipelineConfig'模型的模块."""

from __future__ import annotations

from devtools import pformat
from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from ai.components.graphrag.index.config.cache import PipelineCacheConfigTypes
from ai.components.graphrag.index.config.input import PipelineInputConfigTypes
from ai.components.graphrag.index.config.reporting import PipelineReportingConfigTypes
from ai.components.graphrag.index.config.storage import PipelineStorageConfigTypes
from ai.components.graphrag.index.config.workflow import PipelineWorkflowReference


class PipelineConfig(BaseModel):
    """表示管道的配置."""

    def __repr__(self) -> str:
        """获取字符串表示形式."""
        return pformat(self, highlight=False)

    def __str__(self):
        """获取字符串表示形式."""
        return str(self.model_dump_json(indent=4))

    extends: list[str] | str | None = pydantic_Field(
        description="Extends another pipeline configuration", default=None
    )
    """扩展另一个管道配置"""

    input: PipelineInputConfigTypes | None = pydantic_Field(
        default=None, discriminator="file_type"
    )
    """管道的输入配置."""

    reporting: PipelineReportingConfigTypes | None = pydantic_Field(
        default=None, discriminator="type"
    )
    """管道的报告配置."""

    storage: PipelineStorageConfigTypes | None = pydantic_Field(
        default=None, discriminator="type"
    )
    """管道的存储配置."""

    cache: PipelineCacheConfigTypes | None = pydantic_Field(
        default=None, discriminator="type"
    )
    """管道的缓存配置."""

    root_dir: str | None = pydantic_Field(
        description="The root directory for the pipeline. All other paths will be based on this root_dir.",
        default=None,
    )
    """管道的根目录."""

    workflows: list[PipelineWorkflowReference] = pydantic_Field(
        description="The workflows for the pipeline.", default_factory=list
    )
    """管道的工作流."""
