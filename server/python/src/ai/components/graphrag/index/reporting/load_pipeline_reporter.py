"""加载管道报告器的方法."""

from pathlib import Path
from typing import cast

from datashaper import WorkflowCallbacks

from ai.components.graphrag.config import ReportingType
from ai.components.graphrag.index.config import (
    PipelineBlobReportingConfig,
    PipelineFileReportingConfig,
    PipelineReportingConfig,
)
from ai.components.graphrag.index.reporting.console_workflow_callbacks import (
    ConsoleWorkflowCallbacks,
)
from ai.components.graphrag.index.reporting.file_workflow_callbacks import (
    FileWorkflowCallbacks,
)


def load_pipeline_reporter(
    config: PipelineReportingConfig | None, root_dir: str | None
) -> WorkflowCallbacks:
    """为给定的管道配置创建报告器."""
    config = config or PipelineFileReportingConfig(base_dir="reports")

    path_prefix = ""

    if root_dir is not None:
        from ai.components.graphrag.webserver.utils.rag_util import (
            build_minio_path_prefix,
        )

        path_prefix = build_minio_path_prefix(root_dir)

    match config.type:
        case ReportingType.file | ReportingType.minio:
            config = cast("PipelineFileReportingConfig", config)
            return FileWorkflowCallbacks(
                str(Path(root_dir or "") / (config.base_dir or ""))
            )
        case ReportingType.console:
            return ConsoleWorkflowCallbacks()
        case ReportingType.blob:
            config = cast("PipelineBlobReportingConfig", config)
            # 延迟导入 BlobWorkflowCallbacks
            from ai.components.graphrag.index.reporting.blob_workflow_callbacks import (
                BlobWorkflowCallbacks,
            )

            return BlobWorkflowCallbacks(
                config.connection_string,
                config.container_name,
                base_dir=config.base_dir,
                storage_account_blob_url=config.storage_account_blob_url,
            )
        case _:
            msg = f"Unknown reporting type: {config.type}"
            raise ValueError(msg)
