"""包含'PipelineInputConfig','PipelineCSVInputConfig'和'PipelineTextInputConfig'模型的模块."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from ai.components.graphrag.config.enums import InputFileType, InputType
from ai.components.graphrag.index.config.workflow import PipelineWorkflowStep

T = TypeVar("T")


class PipelineInputConfig(BaseModel, Generic[T]):
    """表示输入的配置."""

    file_type: T
    """输入的文件类型."""

    type: InputType | None = pydantic_Field(
        description="The input type to use.",
        default=None,
    )
    """要使用的输入类型."""

    connection_string: str | None = pydantic_Field(
        description="The blob cache connection string for the input files.",
        default=None,
    )
    """输入文件的blob缓存连接字符串."""

    storage_account_blob_url: str | None = pydantic_Field(
        description="The storage account blob url for the input files.", default=None
    )
    """输入文件的存储账户blob URL."""

    container_name: str | None = pydantic_Field(
        description="The container name for input files.", default=None
    )
    """输入文件的容器名称."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the input files.", default=None
    )
    """输入文件的基础目录."""

    file_pattern: str = pydantic_Field(
        description="The regex file pattern for the input files."
    )
    """输入文件的正则表达式文件模式."""

    file_filter: dict[str, str] | None = pydantic_Field(
        description="The optional file filter for the input files.", default=None
    )
    """输入文件的可选文件过滤器."""

    post_process: list[PipelineWorkflowStep] | None = pydantic_Field(
        description="The post processing steps for the input.", default=None
    )
    """输入的后处理步骤."""

    encoding: str | None = pydantic_Field(
        description="The encoding for the input files.", default=None
    )
    """输入文件的编码."""

    endpoint: str | None = pydantic_Field(
        description="The MinIO endpoint for the storage.", default=None
    )
    """存储的MinIO端点."""

    access_key: str | None = pydantic_Field(
        description="The MinIO access key for the storage.", default=None
    )
    """存储的MinIO访问密钥."""

    secret_key: str | None = pydantic_Field(
        description="The MinIO secret key for the storage.", default=None
    )
    """存储的MinIO秘密密钥."""

    secure: bool | None = pydantic_Field(
        description="Whether to use HTTPS for MinIO connection.", default=True
    )
    """是否对MinIO连接使用HTTPS."""

    region: str | None = pydantic_Field(
        description="The MinIO region for the input.", default=None
    )
    """输入的MinIO区域."""

    enable_virtual_style_endpoint: bool | None = pydantic_Field(
        description="Whether to enable virtual style endpoint for oss. 目前阿里云和腾讯云对象存储都只能是enable_virtual_style_endpoint访问方式, 而minio默认必须是disable_virtual_style_endpoint方式",
        default=None,
    )


class PipelineCSVInputConfig(PipelineInputConfig[Literal[InputFileType.csv]]):
    """表示CSV输入的配置."""

    file_type: Literal[InputFileType.csv] = InputFileType.csv

    source_column: str | None = pydantic_Field(
        description="The column to use as the source of the document.", default=None
    )
    """用作文档来源的列."""

    timestamp_column: str | None = pydantic_Field(
        description="The column to use as the timestamp of the document.", default=None
    )
    """用作文档时间戳的列."""

    timestamp_format: str | None = pydantic_Field(
        description="The format of the timestamp column, so it can be parsed correctly.",
        default=None,
    )
    """时间戳列的格式,以便能够正确解析."""

    text_column: str | None = pydantic_Field(
        description="The column to use as the text of the document.", default=None
    )
    """用作文档文本的列."""

    title_column: str | None = pydantic_Field(
        description="The column to use as the title of the document.", default=None
    )
    """用作文档标题的列."""


class PipelineTextInputConfig(PipelineInputConfig[Literal[InputFileType.text]]):
    """表示文本输入的配置."""

    file_type: Literal[InputFileType.text] = InputFileType.text

    # Text Specific
    title_text_length: int | None = pydantic_Field(
        description="Number of characters to use from the text as the title.",
        default=None,
    )
    """从文本中用作标题的字符数."""


PipelineInputConfigTypes = PipelineCSVInputConfig | PipelineTextInputConfig
"""表示可在管道中使用的输入类型."""
